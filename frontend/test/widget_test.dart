import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:video_platform/main.dart';

void main() {
  testWidgets('应用启动测试', (WidgetTester tester) async {
    // 构建应用
    await tester.pumpWidget(const VideoPlatformApp());

    // 验证标题显示
    expect(find.text('企业内部短视频平台'), findsWidgets);
  });
}
