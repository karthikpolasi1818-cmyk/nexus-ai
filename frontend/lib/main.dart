import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const NexusApp());
}

// ============================================================
// CONFIG
// ============================================================

const String apiBaseUrl = String.fromEnvironment(
  'NEXUS_API_BASE_URL',
  defaultValue: 'http://127.0.0.1:8000',
);
const String fallbackVersion = '6.9.1';

// ============================================================
// FILE MODEL
// ============================================================

class NexusFile {
  final String name;
  final Uint8List bytes;

  const NexusFile({required this.name, required this.bytes});
}

// ============================================================
// API
// ============================================================

class NexusApi {
  static Uri endpoint(String path) {
    return Uri.parse('$apiBaseUrl$path');
  }

  static Future<dynamic> decode(http.Response response) async {
    final body = response.body.trim();

    dynamic data;

    if (body.isNotEmpty) {
      try {
        data = jsonDecode(body);
      } on FormatException catch (error) {
        throw FormatException(
          'NEXUS returned invalid JSON '
          '(HTTP ${response.statusCode}): $error',
        );
      }
    }

    if (response.statusCode < 200 || response.statusCode >= 300) {
      String message = 'HTTP ${response.statusCode}';

      if (data is Map && data['detail'] != null) {
        message = data['detail'].toString();
      } else if (body.isNotEmpty) {
        message = body.length > 1200 ? '${body.substring(0, 1200)}...' : body;
      }

      throw Exception(message);
    }

    if (data == null) {
      throw Exception(
        'NEXUS returned an empty response '
        '(HTTP ${response.statusCode}).',
      );
    }

    return data;
  }

  // ----------------------------------------------------------
  // HEALTH
  // ----------------------------------------------------------

  static Future<Map<String, dynamic>> health() async {
    try {
      final response = await http
          .get(
            endpoint('/health'),
            headers: const {'Accept': 'application/json'},
          )
          .timeout(const Duration(seconds: 15));

      final data = await decode(response);

      if (data is! Map) {
        throw Exception('Invalid backend health response.');
      }

      return Map<String, dynamic>.from(data);
    } on http.ClientException catch (error) {
      throw Exception(
        'Cannot connect to NEXUS backend at '
        '$apiBaseUrl: $error',
      );
    } on FormatException catch (error) {
      throw Exception('Backend health returned invalid JSON: $error');
    } on TimeoutException {
      throw Exception('Backend health check timed out after 15 seconds.');
    } catch (error) {
      throw Exception('Backend health check failed: $error');
    }
  }

  // ----------------------------------------------------------
  // ANALYZE
  // ----------------------------------------------------------

  static Future<Map<String, dynamic>> analyze({
    required List<NexusFile> files,
  }) async {
    if (files.isEmpty) {
      throw Exception('No files selected.');
    }

    final request = http.MultipartRequest('POST', endpoint('/analyze'));

    request.headers['Accept'] = 'application/json';

    // IMPORTANT:
    // Do NOT manually set Content-Type here.
    // MultipartRequest creates the boundary automatically.
    for (final file in files) {
      if (file.bytes.isEmpty) {
        throw Exception('Selected file is empty: ${file.name}');
      }

      request.files.add(
        http.MultipartFile.fromBytes('files', file.bytes, filename: file.name),
      );
    }

    try {
      final streamedResponse = await request.send().timeout(
        const Duration(minutes: 15),
      );

      final response = await http.Response.fromStream(streamedResponse);

      final data = await decode(response);

      if (data is! Map) {
        throw Exception('NEXUS returned an invalid analysis response.');
      }

      return Map<String, dynamic>.from(data);
    } on http.ClientException catch (error) {
      throw Exception(
        'Browser could not complete the request to '
        '$apiBaseUrl/analyze.\n'
        'Browser error: $error',
      );
    } on TimeoutException {
      throw Exception('NEXUS analysis timed out after 15 minutes.');
    } on FormatException catch (error) {
      throw Exception('NEXUS returned invalid JSON: $error');
    } catch (error) {
      throw Exception('NEXUS analysis request failed: $error');
    }
  }
}

// ============================================================
// APP
// ============================================================

class NexusApp extends StatelessWidget {
  const NexusApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'NEXUS AI',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF060B12),
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF00D4FF),
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
      ),
      home: const NexusHomePage(),
    );
  }
}

// ============================================================
// HOME
// ============================================================

class NexusHomePage extends StatefulWidget {
  const NexusHomePage({super.key});

  @override
  State<NexusHomePage> createState() => _NexusHomePageState();
}

class _NexusHomePageState extends State<NexusHomePage> {
  NexusFile? selectedFile;
  List<NexusFile> selectedFiles = [];

  Map<String, dynamic>? analysis;
  Map<String, dynamic>? healthData;

  bool backendOnline = false;
  bool loading = false;

  String status = 'NEXUS AI is ready.';

  String lastError = '';

  String detectedVersion = fallbackVersion;

  int page = 0;

  @override
  void initState() {
    super.initState();
    checkBackend();
  }

  // ==========================================================
  // HEALTH CHECK
  // ==========================================================

  Future<void> checkBackend() async {
    try {
      final result = await NexusApi.health();

      if (!mounted) return;

      final version = firstString(result, [
        'version',
        'engine_version',
        'api_version',
      ]);

      setState(() {
        backendOnline = true;
        healthData = result;

        detectedVersion = version.isNotEmpty ? version : fallbackVersion;

        status = 'NEXUS AI backend is online.';
      });
    } catch (_) {
      if (!mounted) return;

      setState(() {
        backendOnline = false;
        healthData = null;
        status = 'Backend offline. Start FastAPI.';
      });
    }
  }

  // ==========================================================
  // FILE PICKER
  // ==========================================================

  Future<void> pickDataset() async {
    try {
      final result = await FilePicker.pickFiles(
        type: FileType.custom,
        allowedExtensions: [
          'csv',
          'tsv',
          'xlsx',
          'xls',
          'json',
          'parquet',
          'txt',
          'pdf',
          'docx',
          'pptx',
          'html',
          'htm',
        ],
      );

      if (result.isEmpty) {
        return;
      }

      final files = <NexusFile>[];

      for (final file in result) {
        final bytes = await file.readAsBytes();

        if (bytes.isEmpty) {
          throw Exception('Could not read the selected file: ${file.name}');
        }

        files.add(NexusFile(name: file.name, bytes: bytes));
      }

      if (!mounted) return;

      setState(() {
        selectedFiles = files;
        selectedFile = files.first;

        analysis = null;
        lastError = '';
        page = 0;

        status =
            '${files.length} file${files.length == 1 ? '' : 's'} selected. Ready for autonomous analysis.';
      });
    } catch (error) {
      showError('File selection failed: $error');
    }
  }

  Map<String, dynamic> normalizeAnalysisResult(Map<String, dynamic> response) {
    Map<String, dynamic> asMap(dynamic value) {
      if (value is Map) {
        return Map<String, dynamic>.from(
          value.map((key, value) => MapEntry(key.toString(), value)),
        );
      }
      return <String, dynamic>{};
    }

    num asNum(dynamic value) {
      if (value is num) return value;
      return num.tryParse('${value ?? ''}') ?? 0;
    }

    final results = asMap(response['results']);
    final intelligence = asMap(results['intelligence']);
    final metadata = asMap(intelligence['metadata']);
    final rawKpis = asMap(intelligence['kpis']);

    Map<String, dynamic> findKpi(List<String> candidates) {
      for (final candidate in candidates) {
        final direct = rawKpis[candidate];
        if (direct is Map) {
          return asMap(direct);
        }

        for (final entry in rawKpis.entries) {
          if (entry.key.toLowerCase() == candidate.toLowerCase()) {
            return asMap(entry.value);
          }
        }
      }

      return <String, dynamic>{};
    }

    final salesKpi = findKpi(['Sales', 'sales', 'Revenue', 'revenue']);

    final profitKpi = findKpi(['Profit', 'profit', 'Net Profit', 'net_profit']);

    final totalSales = asNum(
      salesKpi['sum'] ?? salesKpi['total'] ?? salesKpi['average'],
    );

    final netProfit = asNum(profitKpi['sum'] ?? profitKpi['total'] ?? 0);

    final totalLoss = asNum(0);

    final lossRate = totalSales == 0 ? 0 : (totalLoss / totalSales) * 100;

    final netMargin = totalSales == 0 ? 0 : (netProfit / totalSales) * 100;

    final rows = asNum(
      metadata['rows'] ?? results['api_metadata']?['rows'] ?? response['rows'],
    );

    final distributions = asMap(intelligence['distributions']);

    final correlations = intelligence['correlations'] is List
        ? List<dynamic>.from(intelligence['correlations'])
        : <dynamic>[];

    final outliers = asMap(intelligence['outliers']);

    final drivers = asMap(intelligence['drivers']);

    final risks = intelligence['risks'] is List
        ? List<dynamic>.from(intelligence['risks'])
        : <dynamic>[];

    final recommendations = intelligence['recommendations'] is List
        ? List<dynamic>.from(intelligence['recommendations'])
        : <dynamic>[];

    final decision = asMap(intelligence['decision_intelligence']);

    final mlReadiness = asMap(intelligence['ml_readiness']);

    final mlScore = asNum(mlReadiness['score']);

    final anomalyCount = outliers.values.fold<num>(0, (sum, value) {
      final item = asMap(value);
      return sum + asNum(item['count']);
    });

    final anomalyPercentage = rows == 0 ? 0 : (anomalyCount / rows) * 100;

    final target = metadata['target'] ?? intelligence['target_analysis'] is Map
        ? asMap(intelligence['target_analysis'])['target']
        : null;

    final systemStatus = <String, dynamic>{
      'profiling': metadata.isNotEmpty || intelligence['schema'] != null,

      'statistics': distributions.isNotEmpty || correlations.isNotEmpty,

      'predictive': mlReadiness.isNotEmpty,

      'anomaly': outliers.isNotEmpty,

      'root_cause': risks.isNotEmpty || recommendations.isNotEmpty,

      'causal': intelligence['causal'] != null,

      'decision': decision.isNotEmpty,
    };

    final predictive = <String, dynamic>{
      'target': target,
      'problem_type': mlReadiness['status'] ?? 'Dataset assessment',

      'best_model': mlReadiness['ready_for_ml'] == true
          ? 'ML-ready dataset'
          : 'Preparation required',

      'reliability': mlScore,

      'top_features': drivers['drivers'] ?? <dynamic>[],
    };

    final statistics = <String, dynamic>{
      'distributions': distributions,

      'correlations': correlations,

      'insights': <dynamic>[
        if (correlations.isNotEmpty)
          'Strong numeric relationships were detected in the dataset.',
        if (distributions.isNotEmpty)
          'Distribution statistics were generated for numeric columns.',
      ],
    };

    final anomaly = <String, dynamic>{
      'iqr': outliers,

      'isolation_forest': <String, dynamic>{},

      'anomaly_count': anomalyCount,

      'anomaly_percentage': anomalyPercentage,
    };

    final rootCause = <String, dynamic>{
      'risks': risks,

      'recommendations': recommendations,
    };

    final decisions = recommendations
        .whereType<Map>()
        .map(
          (item) => <String, dynamic>{
            'priority': item['priority'] ?? 'Medium',
            'decision':
                item['action'] ?? item['category'] ?? 'Review recommendation',
            'category': item['category'] ?? 'Analysis',
          },
        )
        .toList();

    final decisionNormalized = <String, dynamic>{
      ...decision,

      if (!decision.containsKey('decisions')) 'decisions': decisions,
    };

    final kpis = <String, dynamic>{
      ...rawKpis,

      'total_sales': totalSales,

      'net_profit': netProfit,

      'total_loss': totalLoss,

      'loss_rate_pct': lossRate,

      'net_margin': netMargin,
    };

    final profitLoss = <String, dynamic>{
      'total_sales': totalSales,

      'net_profit': netProfit,

      'total_loss': totalLoss,

      'loss_rate_pct': lossRate,

      'net_margin': netMargin,
    };

    final normalized = <String, dynamic>{
      ...response,

      'version': metadata['version'] ?? response['version'] ?? '4.2.0',

      'metadata': metadata,

      'kpis': kpis,

      'profit_loss': profitLoss,

      'system_status': systemStatus,

      'engine_errors': <String, dynamic>{},

      'predictive_intelligence': predictive,

      'statistics': statistics,

      'anomaly': anomaly,

      'root_cause': rootCause,

      'causal': asMap(intelligence['causal']),

      'decision_intelligence': decisionNormalized,
    };

    return normalized;
  }

  // ==========================================================
  // ANALYZE
  // ==========================================================

  Future<void> runAnalysis() async {
    final files = selectedFiles;

    if (files.isEmpty) {
      showError('Please select at least one file first.');
      return;
    }

    if (!backendOnline) {
      await checkBackend();

      if (!backendOnline) {
        showError('Backend is offline. Start FastAPI first.');
        return;
      }
    }

    setState(() {
      loading = true;
      lastError = '';
      status =
          'NEXUS 6.9.1 is analyzing ${files.length} file${files.length == 1 ? '' : 's'}...';
    });

    try {
      final result = await NexusApi.analyze(files: files);

      if (!mounted) return;

      final version = firstString(result, [
        'version',
        'engine_version',
        'api_version',
      ]);

      setState(() {
        analysis = normalizeAnalysisResult(result);
        loading = false;
        page = 1;

        detectedVersion = version.isNotEmpty ? version : fallbackVersion;

        status = 'Autonomous analysis completed successfully.';
      });
    } catch (error) {
      if (!mounted) return;

      final errorText = error.toString();

      setState(() {
        loading = false;
        lastError = errorText;
        status = 'Analysis failed.';
      });

      showError('Analysis failed: $errorText');
    }
  }

  // ==========================================================
  // HELPERS
  // ==========================================================

  double number(dynamic value) {
    if (value is num) {
      return value.toDouble();
    }

    return double.tryParse(value?.toString() ?? '') ?? 0;
  }

  String money(dynamic value) {
    final number = value is num
        ? value.toDouble()
        : double.tryParse('${value ?? ''}') ?? 0;

    return 'INR ${number.toStringAsFixed(2)}';
  }

  String percent(dynamic value) {
    return '${number(value).toStringAsFixed(2)}%';
  }

  String textValue(dynamic value, {String fallback = '-'}) {
    if (value == null) {
      return fallback;
    }

    final text = value.toString();

    if (text.trim().isEmpty) {
      return fallback;
    }

    return text;
  }

  String firstString(Map<String, dynamic>? map, List<String> keys) {
    if (map == null) {
      return '';
    }

    for (final key in keys) {
      final value = map[key];

      if (value != null && value.toString().trim().isNotEmpty) {
        return value.toString();
      }
    }

    return '';
  }

  Map<String, dynamic> mapValue(dynamic value) {
    if (value is Map) {
      return Map<String, dynamic>.from(value);
    }

    return {};
  }

  List<dynamic> listValue(dynamic value) {
    if (value is List) {
      return value;
    }

    return [];
  }

  dynamic nestedValue(dynamic value, List<String> keys) {
    if (value is Map) {
      for (final key in keys) {
        if (value[key] != null) {
          return value[key];
        }
      }
    }
    return null;
  }

  String displayNumber(dynamic value, {String fallback = '-'}) {
    if (value == null) return fallback;
    if (value is num) return value.toStringAsFixed(4);
    final parsed = double.tryParse(value.toString());
    return parsed == null ? value.toString() : parsed.toStringAsFixed(4);
  }

  void showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message, maxLines: 8, overflow: TextOverflow.ellipsis),
        duration: const Duration(seconds: 8),
      ),
    );
  }

  // ==========================================================
  // BUILD
  // ==========================================================

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Row(
        children: [
          buildSidebar(),
          Expanded(
            child: Column(
              children: [
                buildTopBar(),
                Expanded(child: page == 0 ? buildDashboard() : buildAnalysis()),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ==========================================================
  // SIDEBAR
  // ==========================================================

  Widget buildSidebar() {
    return Container(
      width: 240,
      color: const Color(0xFF080E16),
      child: Column(
        children: [
          const SizedBox(height: 30),

          const Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.psychology, color: Color(0xFF00D4FF), size: 30),
              SizedBox(width: 10),
              Text(
                'NEXUS AI',
                style: TextStyle(fontSize: 21, fontWeight: FontWeight.bold),
              ),
            ],
          ),

          const SizedBox(height: 35),

          navItem(Icons.dashboard_outlined, 'Dashboard', 0),

          navItem(Icons.analytics_outlined, 'Data Analysis', 1),

          const Spacer(),

          Padding(
            padding: const EdgeInsets.all(18),
            child: Text(
              'API $detectedVersion\n'
              'Engine $detectedVersion',
              style: const TextStyle(color: Color(0xFF66788B), fontSize: 12),
            ),
          ),
        ],
      ),
    );
  }

  Widget navItem(IconData icon, String title, int index) {
    final selected = page == index;

    return InkWell(
      onTap: () {
        setState(() {
          page = index;
        });
      },
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
        padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 13),
        decoration: BoxDecoration(
          color: selected ? const Color(0xFF102B3D) : Colors.transparent,
          borderRadius: BorderRadius.circular(9),
        ),
        child: Row(
          children: [
            Icon(
              icon,
              color: selected
                  ? const Color(0xFF00D4FF)
                  : const Color(0xFF8192A5),
            ),
            const SizedBox(width: 12),
            Text(
              title,
              style: TextStyle(
                color: selected ? Colors.white : const Color(0xFF94A2B3),
                fontWeight: selected ? FontWeight.w600 : FontWeight.normal,
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ==========================================================
  // TOP BAR
  // ==========================================================

  Widget buildTopBar() {
    return Container(
      height: 72,
      padding: const EdgeInsets.symmetric(horizontal: 25),
      decoration: const BoxDecoration(
        color: Color(0xFF080E16),
        border: Border(bottom: BorderSide(color: Color(0xFF182330))),
      ),
      child: Row(
        children: [
          Text(
            page == 0 ? 'Dashboard' : 'NEXUS 6.9.1 Decision Intelligence',
            style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w600),
          ),

          const Spacer(),

          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            decoration: BoxDecoration(
              color: backendOnline
                  ? const Color(0xFF09271C)
                  : const Color(0xFF2A1414),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Row(
              children: [
                Container(
                  width: 8,
                  height: 8,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: backendOnline
                        ? const Color(0xFF45E69A)
                        : Colors.redAccent,
                  ),
                ),

                const SizedBox(width: 8),

                Text(backendOnline ? 'Backend Online' : 'Backend Offline'),
              ],
            ),
          ),

          IconButton(
            onPressed: loading ? null : checkBackend,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
    );
  }

  // ==========================================================
  // DASHBOARD
  // ==========================================================

  Widget buildDashboard() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(30),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Autonomous Enterprise Intelligence',
            style: TextStyle(fontSize: 30, fontWeight: FontWeight.bold),
          ),

          const SizedBox(height: 8),

          const Text(
            'Upload business data and let NEXUS discover patterns, risks, profit, loss and decisions from the actual dataset.',
            style: TextStyle(color: Color(0xFF8FA0B2), fontSize: 15),
          ),

          const SizedBox(height: 28),

          buildStatusCards(),

          const SizedBox(height: 25),

          buildUploadCard(),

          const SizedBox(height: 25),

          buildBackendInfo(),
        ],
      ),
    );
  }

  // ==========================================================
  // STATUS
  // ==========================================================

  Widget buildStatusCards() {
    final metadata = mapValue(analysis?['metadata']);

    return Row(
      children: [
        Expanded(
          child: statCard(
            'API',
            backendOnline ? 'ONLINE' : 'OFFLINE',
            Icons.cloud_done,
          ),
        ),

        const SizedBox(width: 14),

        Expanded(child: statCard('ENGINE', detectedVersion, Icons.memory)),

        const SizedBox(width: 14),

        Expanded(
          child: statCard(
            'ROWS',
            metadata['rows'] == null ? '-' : textValue(metadata['rows']),
            Icons.table_chart,
          ),
        ),

        const SizedBox(width: 14),

        Expanded(
          child: statCard(
            'STATUS',
            analysis == null ? 'READY' : 'COMPLETE',
            Icons.insights,
          ),
        ),
      ],
    );
  }

  Widget statCard(String title, String value, IconData icon) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF0B141E),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF182A39)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: const Color(0xFF00D4FF)),
          const SizedBox(height: 12),
          Text(
            title,
            style: const TextStyle(color: Color(0xFF71869B), fontSize: 11),
          ),
          const SizedBox(height: 5),
          Text(
            value,
            style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }

  // ==========================================================
  // BACKEND INFO
  // ==========================================================

  Widget buildBackendInfo() {
    return card(
      'NEXUS System',
      Icons.memory,
      Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          infoRow('Backend', apiBaseUrl),
          infoRow('API status', backendOnline ? 'ONLINE' : 'OFFLINE'),
          infoRow('NEXUS version', detectedVersion),
          infoRow(
            'Analysis',
            analysis == null ? 'Waiting for dataset' : 'Dataset analyzed',
          ),
        ],
      ),
    );
  }

  Widget infoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        children: [
          SizedBox(
            width: 150,
            child: Text(
              label,
              style: const TextStyle(color: Color(0xFF71869B)),
            ),
          ),
          Expanded(
            child: SelectableText(
              value,
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
          ),
        ],
      ),
    );
  }

  // ==========================================================
  // UPLOAD CARD
  // ==========================================================

  Widget buildUploadCard() {
    return card(
      'Autonomous Analysis',
      Icons.rocket_launch,
      Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            selectedFiles.isEmpty
                ? 'Select one or more supported files.'
                : '${selectedFiles.length} file${selectedFiles.length == 1 ? '' : 's'} selected',
            style: const TextStyle(color: Color(0xFF9BAABC)),
          ),

          if (selectedFiles.isNotEmpty) ...[
            const SizedBox(height: 8),

            ...selectedFiles.map(
              (file) => Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Text(
                  'â€¢ ${file.name} â€” ${formatBytes(file.bytes.length)}',
                  style: const TextStyle(
                    color: Color(0xFF65798D),
                    fontSize: 12,
                  ),
                ),
              ),
            ),
          ],

          const SizedBox(height: 20),

          Wrap(
            spacing: 12,
            runSpacing: 12,
            children: [
              ElevatedButton.icon(
                onPressed: loading ? null : pickDataset,
                icon: const Icon(Icons.upload_file),
                label: const Text('Select Files'),
              ),

              ElevatedButton.icon(
                onPressed: selectedFiles.isEmpty || loading
                    ? null
                    : runAnalysis,
                icon: loading
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.auto_awesome),
                label: Text(
                  loading ? 'Analyzing...' : 'Run Autonomous Analysis',
                ),
              ),

              if (selectedFiles.isNotEmpty)
                OutlinedButton.icon(
                  onPressed: loading
                      ? null
                      : () {
                          setState(() {
                            selectedFile = null;
                            selectedFiles = [];
                            analysis = null;
                            lastError = '';
                            page = 0;
                            status = 'Selected files cleared.';
                          });
                        },
                  icon: const Icon(Icons.delete_outline),
                  label: const Text('Clear'),
                ),
            ],
          ),

          const SizedBox(height: 15),

          Text(
            status,
            style: TextStyle(
              color: loading
                  ? const Color(0xFF00D4FF)
                  : const Color(0xFF71859A),
            ),
          ),

          if (lastError.isNotEmpty) ...[
            const SizedBox(height: 12),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: const Color(0xFF2A1414),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(
                  color: Colors.redAccent.withValues(alpha: 0.45),
                ),
              ),
              child: SelectableText(
                lastError,
                style: const TextStyle(color: Colors.redAccent, height: 1.4),
              ),
            ),
          ],
        ],
      ),
    );
  }

  // ==========================================================
  // ANALYSIS
  // ==========================================================

  Widget buildAnalysis() {
    if (analysis == null) {
      return const Center(child: Text('Upload a dataset and run NEXUS AI.'));
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(30),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'NEXUS AI 6.9.1 Decision Intelligence',
            style: TextStyle(fontSize: 29, fontWeight: FontWeight.bold),
          ),

          const SizedBox(height: 8),

          Text(
            selectedFiles.isEmpty
                ? 'Dataset'
                : '${selectedFiles.length} file${selectedFiles.length == 1 ? '' : 's'} analyzed',
            style: const TextStyle(color: Color(0xFF8093A7)),
          ),

          const SizedBox(height: 25),

          buildKpis(),

          const SizedBox(height: 25),

          buildEngineStatus(),

          const SizedBox(height: 25),

          buildExecutiveDecision(),

          const SizedBox(height: 25),

          buildDecisions(),

          const SizedBox(height: 25),

          buildLossDrivers(),

          const SizedBox(height: 25),

          buildPredictive(),

          const SizedBox(height: 25),

          buildStatistics(),

          const SizedBox(height: 25),

          buildAnomaly(),

          const SizedBox(height: 25),

          buildCausal(),

          const SizedBox(height: 25),

          buildRaw(),
        ],
      ),
    );
  }

  // ==========================================================
  // KPIs
  // ==========================================================

  Widget buildKpis() {
    final kpis = mapValue(analysis?['kpis']);

    final fallback = mapValue(analysis?['profit_loss']);

    final metadata = mapValue(analysis?['metadata']);

    return Wrap(
      spacing: 14,
      runSpacing: 14,
      children: [
        metric(
          'Rows',
          textValue(metadata['rows'], fallback: '0'),
          Icons.table_rows,
        ),

        metric(
          'Total Sales',
          money(kpis['total_sales'] ?? fallback['total_sales']),
          Icons.payments,
        ),

        metric(
          'Net Profit',
          money(kpis['net_profit'] ?? fallback['net_profit']),
          Icons.trending_up,
        ),

        metric(
          'Total Loss',
          money(kpis['total_loss'] ?? fallback['total_loss']),
          Icons.trending_down,
        ),

        metric(
          'Loss Rate',
          percent(
            kpis['loss_rate_pct'] ??
                kpis['loss_rate'] ??
                fallback['loss_rate_pct'],
          ),
          Icons.percent,
        ),

        metric(
          'Net Margin',
          percent(kpis['net_margin']),
          Icons.account_balance,
        ),
      ],
    );
  }

  Widget metric(String title, String value, IconData icon) {
    return SizedBox(
      width: 220,
      child: Container(
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          color: const Color(0xFF0B141E),
          borderRadius: BorderRadius.circular(13),
          border: Border.all(color: const Color(0xFF1A2B3A)),
        ),
        child: Row(
          children: [
            Icon(icon, color: const Color(0xFF00D4FF)),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: const TextStyle(
                      color: Color(0xFF7F91A4),
                      fontSize: 12,
                    ),
                  ),
                  const SizedBox(height: 5),
                  Text(
                    value,
                    style: const TextStyle(
                      fontSize: 17,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ==========================================================
  // ENGINE STATUS
  // ==========================================================

  Widget buildEngineStatus() {
    final system = mapValue(analysis?['system_status']);

    final errors = mapValue(analysis?['engine_errors']);

    const engines = [
      'profiling',
      'statistics',
      'predictive',
      'anomaly',
      'root_cause',
      'causal',
      'decision',
    ];

    return card(
      'NEXUS Intelligence Engines',
      Icons.memory,
      Column(
        children: [
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: engines.map((engine) {
              final active = system[engine] == true;

              return Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 13,
                  vertical: 9,
                ),
                decoration: BoxDecoration(
                  color: active
                      ? const Color(0xFF09271C)
                      : const Color(0xFF2A1414),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      active ? Icons.check_circle : Icons.error,
                      size: 16,
                      color: active
                          ? const Color(0xFF45E69A)
                          : Colors.redAccent,
                    ),
                    const SizedBox(width: 6),
                    Text(engine),
                  ],
                ),
              );
            }).toList(),
          ),

          if (errors.isNotEmpty) ...[
            const SizedBox(height: 18),

            const Align(
              alignment: Alignment.centerLeft,
              child: Text(
                'Engine Errors',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
            ),

            const SizedBox(height: 8),

            ...errors.entries.map(
              (entry) => Padding(
                padding: const EdgeInsets.only(bottom: 5),
                child: Align(
                  alignment: Alignment.centerLeft,
                  child: Text(
                    '${entry.key}: ${entry.value}',
                    style: const TextStyle(color: Colors.redAccent),
                  ),
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  // ==========================================================
  // EXECUTIVE DECISION
  // ==========================================================

  Widget buildExecutiveDecision() {
    final decision = mapValue(analysis?['decision_intelligence']);

    final summary = mapValue(decision['executive_summary']);

    if (decision.isEmpty) {
      return const SizedBox();
    }

    return card(
      'Executive Decision',
      Icons.psychology,
      Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            textValue(
              summary['headline'],
              fallback: 'Decision intelligence generated.',
            ),
            style: const TextStyle(fontSize: 19, fontWeight: FontWeight.bold),
          ),

          const SizedBox(height: 14),

          Text(
            textValue(summary['recommended_focus']),
            style: const TextStyle(color: Color(0xFF9AAABB), height: 1.4),
          ),

          const SizedBox(height: 14),

          Text(
            'Next step: ${textValue(summary['next_step'])}',
            style: const TextStyle(
              color: Color(0xFF55E7A0),
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  // ==========================================================
  // DECISIONS
  // ==========================================================

  Widget buildDecisions() {
    final decision = mapValue(analysis?['decision_intelligence']);

    final decisions = listValue(decision['decisions']);

    if (decisions.isEmpty) {
      return const SizedBox();
    }

    return card(
      'Prioritized Decisions',
      Icons.flag,
      Column(
        children: decisions.take(10).map((item) {
          final map = mapValue(item);

          return Container(
            width: double.infinity,
            margin: const EdgeInsets.only(bottom: 12),
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: const Color(0xFF0A121B),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        '${map['dimension'] ?? 'Factor'} = ${map['value'] ?? ''}',
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 16,
                        ),
                      ),
                    ),
                    Chip(label: Text(textValue(map['priority']))),
                  ],
                ),

                const SizedBox(height: 8),

                Text('Gross loss: ${money(map['gross_loss'])}'),

                Text('Loss rate: ${percent(map['loss_rate'])}'),

                Text('Confidence: ${textValue(map['confidence'])}'),

                const SizedBox(height: 8),

                Text(
                  textValue(map['recommended_action']),
                  style: const TextStyle(color: Color(0xFF9AAABB), height: 1.4),
                ),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }

  // ==========================================================
  // RCA
  // ==========================================================

  Widget buildLossDrivers() {
    final rca = mapValue(analysis?['root_cause']);

    final drivers = listValue(rca['loss_drivers']);

    if (drivers.isEmpty) {
      return const SizedBox();
    }

    return card(
      'Root Cause Intelligence',
      Icons.search,
      Column(
        children: drivers.take(10).map((item) {
          final map = mapValue(item);

          final displayValue = map['value'] ?? map['driver'];

          final loss = map['gross_loss'] ?? map['loss'];

          return Container(
            width: double.infinity,
            margin: const EdgeInsets.only(bottom: 10),
            padding: const EdgeInsets.all(15),
            decoration: BoxDecoration(
              color: const Color(0xFF0A121B),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '${map['dimension'] ?? 'Factor'} = $displayValue',
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),

                const SizedBox(height: 6),

                Text(
                  'Gross loss: ${money(loss)}',
                  style: const TextStyle(color: Colors.redAccent),
                ),

                const SizedBox(height: 5),

                Text(
                  'Loss rate: ${percent(map['loss_rate'])}',
                  style: const TextStyle(color: Color(0xFF9AAABB)),
                ),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }

  // ==========================================================
  // PREDICTIVE
  // ==========================================================

  Widget buildPredictive() {
    final predictive = mapValue(analysis?['predictive_intelligence']);

    if (predictive.isEmpty) {
      return const SizedBox();
    }

    final metrics = mapValue(predictive['best_model_metrics']);

    final importance = listValue(predictive['permutation_importance']);

    return card(
      'Predictive Intelligence',
      Icons.auto_graph,
      Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          infoRow('Target', textValue(predictive['target'])),

          infoRow('Task', textValue(predictive['problem_type'])),

          infoRow('Best model', textValue(predictive['best_model'])),

          infoRow('Reliability', textValue(predictive['reliability'])),

          if (metrics.isNotEmpty) ...[
            const Divider(),

            const Text(
              'Best Model Metrics',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),

            const SizedBox(height: 8),

            ...metrics.entries.map(
              (entry) => Text('${entry.key}: ${entry.value}'),
            ),
          ],

          if (importance.isNotEmpty) ...[
            const SizedBox(height: 18),

            const Text(
              'Top Predictive Features',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),

            const SizedBox(height: 8),

            ...importance.take(8).map((item) {
              final map = mapValue(item);

              return Padding(
                padding: const EdgeInsets.only(bottom: 5),
                child: Text(
                  '${map['feature'] ?? '-'}: '
                  '${map['importance'] ?? '-'}',
                ),
              );
            }),
          ],
        ],
      ),
    );
  }

  // ==========================================================
  // STATISTICS
  // ==========================================================

  Widget buildStatistics() {
    final statistics = mapValue(analysis?['statistics']);

    if (statistics.isEmpty) {
      return const SizedBox();
    }

    final correlations = listValue(statistics['correlations']);

    final insights = listValue(statistics['insights']);

    return card(
      'Statistical Intelligence',
      Icons.query_stats,
      Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (correlations.isNotEmpty) ...[
            const Text(
              'Target Correlations',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),

            const SizedBox(height: 10),

            ...correlations.take(10).map((item) {
              final map = mapValue(item);

              return Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Text(
                  '${map['variable_1'] ?? '-'} ? '
                  '${map['variable_2'] ?? '-'}: '
                  '${map['correlation'] ?? '-'} '
                  '${map['strength'] ?? ''}',
                ),
              );
            }),
          ],

          if (insights.isNotEmpty) ...[
            const SizedBox(height: 15),

            const Text(
              'Insights',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),

            const SizedBox(height: 8),

            ...insights
                .take(10)
                .map(
                  (item) => Padding(
                    padding: const EdgeInsets.only(bottom: 6),
                    child: Text(
                      'ï¿½ ${item.toString()}',
                      style: const TextStyle(color: Color(0xFF9AAABB)),
                    ),
                  ),
                ),
          ],
        ],
      ),
    );
  }

  // ==========================================================
  // ANOMALY
  // ==========================================================

  Widget buildAnomaly() {
    final anomaly = mapValue(analysis?['anomaly']);

    if (anomaly.isEmpty) {
      return const SizedBox();
    }

    final iqr = listValue(anomaly['iqr']);

    final isolation = mapValue(anomaly['isolation_forest']);

    return card(
      'Anomaly Intelligence',
      Icons.warning_amber,
      Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (isolation.isNotEmpty)
            infoRow(
              'Isolation Forest',
              textValue(
                isolation['anomaly_count'],
                fallback: textValue(isolation['anomalies']),
              ),
            ),

          if (iqr.isNotEmpty) ...[
            const Text(
              'IQR Anomalies',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),

            const SizedBox(height: 10),

            ...iqr.take(10).map((item) {
              final map = mapValue(item);

              return Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Text(
                  '${map['feature'] ?? '-'} ï¿½ '
                  '${map['anomaly_percentage'] ?? '-'}%',
                ),
              );
            }),
          ],
        ],
      ),
    );
  }

  // ==========================================================
  // CAUSAL
  // ==========================================================

  Widget buildCausal() {
    final causal = mapValue(analysis?['causal']);

    if (causal.isEmpty) {
      return const SizedBox();
    }

    final timing = mapValue(causal['timing_review']);

    final reliability = mapValue(causal['causal_reliability']);

    final reliabilityLevel = nestedValue(reliability, [
      'level',
      'rating',
      'status',
    ]);

    final reliabilityScore = nestedValue(reliability, [
      'score',
      'reliability_score',
      'value',
    ]);

    final dowhy = mapValue(causal['dowhy']);

    final econml = mapValue(causal['econml']);

    final dowhyEffect =
        causal['dowhy_effect'] ??
        nestedValue(dowhy, ['effect', 'estimated_effect', 'ate']);

    final econmlEffect =
        causal['econml_mean_effect'] ??
        nestedValue(econml, ['mean_effect', 'effect', 'ate']);

    final reliabilityText = reliabilityLevel != null
        ? '${textValue(reliabilityLevel)}'
              '${reliabilityScore != null ? ' (${displayNumber(reliabilityScore)}%)' : ''}'
        : textValue(reliability, fallback: 'Not established');

    return card(
      'Causal Intelligence',
      Icons.account_tree,
      Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          infoRow('Treatment', textValue(causal['treatment'])),

          infoRow('Outcome', textValue(causal['outcome'])),

          infoRow('Causal supported', textValue(causal['causal_supported'])),

          infoRow('Reliability', reliabilityText),

          infoRow('Confidence', textValue(causal['confidence'])),

          infoRow('DoWhy effect', displayNumber(dowhyEffect)),

          infoRow('EconML effect', displayNumber(econmlEffect)),

          if (timing.isNotEmpty) ...[
            const SizedBox(height: 15),

            const Text(
              'Timing Review',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),

            const SizedBox(height: 8),

            ...timing.entries.map(
              (entry) => Padding(
                padding: const EdgeInsets.only(bottom: 5),
                child: Text(
                  '${entry.key}: ${entry.value}',
                  style: const TextStyle(color: Color(0xFF9AAABB)),
                ),
              ),
            ),
          ],

          const SizedBox(height: 14),

          const Text(
            'Causal estimates are evidence for investigation and should not be treated as automatic proof of business causality.',
            style: TextStyle(color: Color(0xFFFFB86B), height: 1.4),
          ),
        ],
      ),
    );
  }

  // ==========================================================
  // RAW
  // ==========================================================

  Widget buildRaw() {
    return card(
      'Complete NEXUS 6.9.1 API Response',
      Icons.code,
      SelectableText(
        const JsonEncoder.withIndent('  ').convert(analysis),
        style: const TextStyle(
          fontSize: 12,
          color: Color(0xFF8EA4B7),
          height: 1.4,
        ),
      ),
    );
  }

  // ==========================================================
  // CARD
  // ==========================================================

  Widget card(String title, IconData icon, Widget child) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        color: const Color(0xFF0B141E),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFF1A2B3A)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: const Color(0xFF00D4FF)),

              const SizedBox(width: 10),

              Text(
                title,
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),

          const SizedBox(height: 18),

          child,
        ],
      ),
    );
  }

  // ==========================================================
  // FILE SIZE
  // ==========================================================

  String formatBytes(int bytes) {
    if (bytes < 1024) {
      return '$bytes B';
    }

    if (bytes < 1024 * 1024) {
      return '${(bytes / 1024).toStringAsFixed(1)} KB';
    }

    if (bytes < 1024 * 1024 * 1024) {
      return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
    }

    return '${(bytes / (1024 * 1024 * 1024)).toStringAsFixed(1)} GB';
  }
}
