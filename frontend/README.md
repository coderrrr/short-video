# 企业内部短视频平台 - C端应用

基于 Flutter 的移动端应用，可编译为 Web (H5) 或 Native App。

## 技术栈

- **框架**: Flutter 3.x
- **状态管理**: Provider
- **网络请求**: Dio
- **路由**: go_router
- **视频播放**: video_player, chewie
- **本地存储**: shared_preferences, hive

## 项目结构

```
frontend/
├── lib/
│   ├── main.dart            # 应用入口
│   ├── config/              # 配置文件
│   ├── models/              # 数据模型
│   ├── services/            # API服务
│   ├── providers/           # 状态管理
│   ├── screens/             # 页面
│   ├── widgets/             # 组件
│   └── utils/               # 工具函数
├── test/                    # 测试文件
├── pubspec.yaml             # 依赖配置
└── README.md
```

## 环境设置

### 1. 安装Flutter

参考 [Flutter官方文档](https://flutter.dev/docs/get-started/install) 安装Flutter SDK。

### 2. 安装依赖

```bash
flutter pub get
```

### 3. 配置API地址

在运行时通过环境变量配置API地址：

```bash
flutter run --dart-define=API_BASE_URL=http://localhost:8000
```

## 运行应用

### Web (H5)

```bash
flutter run -d chrome
```

### iOS模拟器

```bash
flutter run -d ios
```

### Android模拟器

```bash
flutter run -d android
```

## 构建应用

### 构建Web版本

```bash
flutter build web
```

构建产物在 `build/web/` 目录下，可以部署到任何Web服务器。

### 构建Android APK

```bash
flutter build apk --release
```

### 构建iOS IPA

```bash
flutter build ios --release
```

## 运行测试

```bash
# 运行所有测试
flutter test

# 运行Widget测试
flutter test test/widget_test.dart

# 生成测试覆盖率报告
flutter test --coverage
```

## Flutter开发指南

### 状态管理

项目使用Provider进行状态管理。主要的Provider包括：

- **AppState**: 全局应用状态（用户信息、认证状态）
- **ContentProvider**: 内容相关状态（推荐列表、搜索结果）
- **UserProvider**: 用户相关状态（个人资料、关注列表）

#### 使用Provider示例

```dart
// 在Widget中读取状态
class MyWidget extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final appState = Provider.of<AppState>(context);
    return Text('当前用户: ${appState.currentUser?.name}');
  }
}

// 使用Consumer优化性能
Consumer<ContentProvider>(
  builder: (context, contentProvider, child) {
    return ListView.builder(
      itemCount: contentProvider.recommendedContent.length,
      itemBuilder: (context, index) {
        return ContentCard(content: contentProvider.recommendedContent[index]);
      },
    );
  },
)
```

### 网络请求

使用Dio进行HTTP请求，已封装在`lib/services/api_client.dart`中。

#### API调用示例

```dart
// 获取推荐内容
final apiClient = ApiClient();
final response = await apiClient.get('/contents/recommended', queryParameters: {
  'page': 1,
  'size': 20,
});

// 上传视频
final formData = FormData.fromMap({
  'video': await MultipartFile.fromFile(videoPath),
  'title': '视频标题',
  'description': '视频描述',
});
final response = await apiClient.post('/contents/upload', data: formData);
```

### 路由管理

使用go_router进行路由管理，配置在`lib/config/routes.dart`中。

#### 路由导航示例

```dart
// 导航到内容详情页
context.go('/content/${contentId}');

// 带参数导航
context.go('/search', extra: {'query': '搜索关键词'});

// 返回上一页
context.pop();
```

### 视频播放

使用video_player和chewie进行视频播放。

#### 视频播放器使用示例

```dart
import 'package:video_player/video_player.dart';
import 'package:chewie/chewie.dart';

class VideoPlayerWidget extends StatefulWidget {
  final String videoUrl;
  
  @override
  _VideoPlayerWidgetState createState() => _VideoPlayerWidgetState();
}

class _VideoPlayerWidgetState extends State<VideoPlayerWidget> {
  late VideoPlayerController _videoController;
  late ChewieController _chewieController;
  
  @override
  void initState() {
    super.initState();
    _videoController = VideoPlayerController.network(widget.videoUrl);
    _chewieController = ChewieController(
      videoPlayerController: _videoController,
      autoPlay: true,
      looping: false,
    );
  }
  
  @override
  Widget build(BuildContext context) {
    return Chewie(controller: _chewieController);
  }
  
  @override
  void dispose() {
    _videoController.dispose();
    _chewieController.dispose();
    super.dispose();
  }
}
```

### 本地存储

使用shared_preferences存储简单数据，使用hive存储复杂数据。

#### 本地存储示例

```dart
// 使用SharedPreferences
import 'package:shared_preferences/shared_preferences.dart';

// 保存数据
final prefs = await SharedPreferences.getInstance();
await prefs.setString('token', 'jwt_token_here');

// 读取数据
final token = prefs.getString('token');

// 使用Hive
import 'package:hive/hive.dart';

// 打开box
final box = await Hive.openBox('settings');

// 保存数据
await box.put('videoQuality', 'HD');

// 读取数据
final quality = box.get('videoQuality', defaultValue: 'SD');
```

### 添加新页面

1. 在 `lib/screens/` 下创建页面文件
2. 在 `lib/providers/` 下创建状态管理（如需要）
3. 在 `lib/config/routes.dart` 中注册路由
4. 编写Widget测试

#### 页面模板

```dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

class MyNewScreen extends StatefulWidget {
  const MyNewScreen({Key? key}) : super(key: key);
  
  @override
  State<MyNewScreen> createState() => _MyNewScreenState();
}

class _MyNewScreenState extends State<MyNewScreen> {
  @override
  void initState() {
    super.initState();
    // 初始化逻辑
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('页面标题'),
      ),
      body: Center(
        child: Text('页面内容'),
      ),
    );
  }
}
```

### 添加新组件

1. 在 `lib/widgets/` 下创建组件文件
2. 使用中文注释说明组件用途
3. 编写Widget测试

#### 组件模板

```dart
import 'package:flutter/material.dart';

/// 内容卡片组件
/// 用于在列表中展示视频内容的预览信息
class ContentCard extends StatelessWidget {
  final Content content;
  final VoidCallback? onTap;
  
  const ContentCard({
    Key? key,
    required this.content,
    this.onTap,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        onTap: onTap,
        child: Column(
          children: [
            // 封面图片
            Image.network(content.coverUrl),
            // 标题和信息
            Padding(
              padding: const EdgeInsets.all(8.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(content.title, style: Theme.of(context).textTheme.titleMedium),
                  Text('${content.viewCount} 次观看'),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
```

### 代码规范

- **命名规范**:
  - 文件名: `snake_case.dart`
  - 类名: `PascalCase`
  - 变量/函数名: `camelCase`
  - 常量: `lowerCamelCase`
- **注释**: 使用中文注释，公共API使用`///`文档注释
- **Widget**: 尽可能使用`const`构造函数提高性能
- **状态管理**: 优先使用Provider，避免过度使用setState
- **异步**: 使用`async/await`，避免回调地狱
- **错误处理**: 使用try-catch处理异步错误

### 性能优化

1. **使用const构造函数**: 减少Widget重建
2. **使用ListView.builder**: 懒加载列表项
3. **图片缓存**: 使用cached_network_image
4. **避免不必要的重建**: 使用Consumer精确控制重建范围
5. **分页加载**: 实现上拉加载更多

### 调试技巧

```bash
# 启动调试模式
flutter run --debug

# 查看Widget树
# 在DevTools中使用Flutter Inspector

# 性能分析
flutter run --profile

# 查看日志
flutter logs
```

## 集成到企业App

### WebView集成

将构建的Web版本集成到企业App的WebView中：

```dart
// 企业App中的WebView配置示例
WebView(
  initialUrl: 'https://your-domain.com/video-platform',
  javascriptMode: JavascriptMode.unrestricted,
)
```

### 原生集成

如果需要更好的性能，可以将Flutter编译为原生模块集成到企业App中。

## 部署

### Web部署

1. 构建Web版本：`flutter build web`
2. 将 `build/web/` 目录上传到S3
3. 配置CloudFront CDN
4. 在企业App中通过WebView加载

### Native App部署

1. 构建对应平台的安装包
2. 通过企业应用商店分发
