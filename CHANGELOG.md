# 📝 Changelog

Latest changes to this project.


### [unreleased]



### 🐛 Bug Fixes

- 更新文档类型匹配规则以支持多种文档标签- ([c63b7d7](https://github.com/sinspired/VpngateClient/commit/c63b7d70453bbdad79b4aadc64f4723fb82c5d1d))




### 1.3.1 - 2025-05-06



### 🐛 Bug Fixes

- 修复Linux系统连接监测错误- ([18522af](https://github.com/sinspired/VpngateClient/commit/18522afdfe9ac703bbc9868ca72a5f8c6e399e55))




### 1.3.0 - 2025-05-06



### 🚀 Features

- *(translations)* 新增日志相关翻译以支持错误处理和状态信息- ([bfceed6](https://github.com/sinspired/VpngateClient/commit/bfceed67407080ec6426080bc0ca03cfaa2a5de2))
- 添加更多翻译，优化界面输出信息- ([50a75e7](https://github.com/sinspired/VpngateClient/commit/50a75e72ee769a721e749682ef8080754ce381e9))



### 🐛 Bug Fixes

- *(translations)* 修改代理运行提示信息，优化VPN服务器加载相关翻译- ([4b2b474](https://github.com/sinspired/VpngateClient/commit/4b2b47457f6b2fd69e57d59cf9704a3f571b9414))
- *(translations)* 优化VPN连接提示信息和日志输出格式- ([544a4a0](https://github.com/sinspired/VpngateClient/commit/544a4a0d73b631320a50a03c0a2444fe7b6984f7))



### ⚡ Performance

- *(args)* 优化参数设置和界面显示- ([6782bad](https://github.com/sinspired/VpngateClient/commit/6782bad4d99d7279d2e6b6d54b666ce0898b63f5))



### ⚙️ Miscellaneous Tasks

- *(config)* 添加tls兼容性设置- ([37d0d24](https://github.com/sinspired/VpngateClient/commit/37d0d24ad600eba2f9e761ac2a01efe949267c20))




### 1.2.0 - 2025-05-04



### 🚀 Features

- 自动根据平台设置tmp,cache,config文件夹- ([7acf2ab](https://github.com/sinspired/VpngateClient/commit/7acf2ab2322cf9d007b80b06f0a85c58bf9e181a))
- 添加节点延迟检测和排序- ([dc81c31](https://github.com/sinspired/VpngateClient/commit/dc81c3100c082810c1417a305225df869d28ab75))



### 🐛 Bug Fixes

- 修复模块导入和setup- ([5a7106d](https://github.com/sinspired/VpngateClient/commit/5a7106da9b2a8036512a5affb33cccaa72fa4fe3))
- 修复windows平台无法使用select进行倒计时的错误- ([e08f32e](https://github.com/sinspired/VpngateClient/commit/e08f32e61d2639fa663f9f1a0cb1d4d626dc7a8d))
- Pyinstaller在根目录下运行时，需要指定导入模块所在路径- ([7e42a29](https://github.com/sinspired/VpngateClient/commit/7e42a2913b4c5483dad4f420048cc6ea767767d2))



### 📚 Documentation

- *(README.md)* 更新使用说明- ([89295fb](https://github.com/sinspired/VpngateClient/commit/89295fbac0eb730988eb05da6702e26742ea4c0a))



### ⚡ Performance

- 优化运行时界面输出- ([ab1e66d](https://github.com/sinspired/VpngateClient/commit/ab1e66df9061c09fd9fc4e7baee58fb4b506bdc0))



### ⚙️ Miscellaneous Tasks

- *(release)* 修改发布流程- ([993437a](https://github.com/sinspired/VpngateClient/commit/993437ab5ca27112eaa4fbf8c29913d76e26824b))
- *(release)* Bump version to 1.2.0- ([8e7eba6](https://github.com/sinspired/VpngateClient/commit/8e7eba6afb751a88e87e550ca3b55ae69dc29d26))




### 1.1.0 - 2025-05-03



### 🚀 Features

- For Windows & bug fix & add new feature- ([ae0ea0c](https://github.com/sinspired/VpngateClient/commit/ae0ea0cd0011775d36b1f6805189103ed2feab83))
- 1.add status monitor;2.add connection speedtest- ([7d3f092](https://github.com/sinspired/VpngateClient/commit/7d3f09298a02cfc7436cd56fa94a5cb574dd84ad))
- Add clean status tempfile,add timeout in speedtest function- ([ddc73a7](https://github.com/sinspired/VpngateClient/commit/ddc73a7069026fd065acd04267d0f8b69b5dc6c8))
- Add new api url- ([cdd3367](https://github.com/sinspired/VpngateClient/commit/cdd3367198dee260c823e3765f0af95e82905ed1))
- 添加更多GitHub代理网址- ([59cbb8c](https://github.com/sinspired/VpngateClient/commit/59cbb8c1f9d89cb0bca546046a03179b0ff0389e))
- 添加连接状态监控，自动切换，自动收藏优质配置等功能- ([8edbb42](https://github.com/sinspired/VpngateClient/commit/8edbb425427dc5ba1f6ef7dfb4968dc7ecface35))



>1. 自动显示下载数据量，显示上行下行速率；



>2. 正常连接一段时间的配置,会自动保存收藏;



>3. 优先连接收藏的配置。



### 🐛 Bug Fixes

- Serverlist download- ([e673274](https://github.com/sinspired/VpngateClient/commit/e67327465394ae6199945fbbcf4e697c7fe4831f))
- 修复github proxy网址- ([0173b35](https://github.com/sinspired/VpngateClient/commit/0173b351b430bb7dc3a750471d4ef72e4820e1b2))
- 跨平台编译- ([e91040a](https://github.com/sinspired/VpngateClient/commit/e91040a8861e9b761ee5aac6c2a92f6e2136f6ba))
- 解决跨平台编译冲突，移除console导入- ([00a1b04](https://github.com/sinspired/VpngateClient/commit/00a1b0430ef32f3b3378341fbf7ed407e754625d))



### ⚙️ Miscellaneous Tasks

- *(release)* Creat release action- ([fc7c081](https://github.com/sinspired/VpngateClient/commit/fc7c0811d87590a83fce2ea325273406393a5235))
- *(config)* Modifiy default min download speed- ([c4e86fb](https://github.com/sinspired/VpngateClient/commit/c4e86fb833c4dea4a54fd4bf27eaf16b4f5b9736))
- Add VpngateClient_global.py- ([e7460c8](https://github.com/sinspired/VpngateClient/commit/e7460c88808352ef49bce24e1f21f7512ab927cb))
- Add more translation- ([d5de135](https://github.com/sinspired/VpngateClient/commit/d5de135108f1637196d5468259c62e8ae43f6a18))
- Add more translation- ([7599092](https://github.com/sinspired/VpngateClient/commit/75990928ed6bc7d08c3e6919cd6a4304422570dc))
- Add more translation- ([c90c405](https://github.com/sinspired/VpngateClient/commit/c90c405e2c4e8a7a07d6ec3c7070cbe66a03c86b))
- 添加logo文件- ([6b9a444](https://github.com/sinspired/VpngateClient/commit/6b9a44404df7bdd4fa4cd532495ae9d6cd2bfb42))
- 清理文件- ([5c1e51e](https://github.com/sinspired/VpngateClient/commit/5c1e51ef058320c85f9c3d6c6fae4b5f312e685e))
- 清理文件- ([c472429](https://github.com/sinspired/VpngateClient/commit/c47242964c58962b3dc3abc37c030aefc9cbd2f1))
- *(release)* Creat_release.yml，deb包申请sudo权限- ([9c0b004](https://github.com/sinspired/VpngateClient/commit/9c0b0043b780821d56d4766134bbac4e0e40927c))




### 0.0.0 - 2025-05-03



### 🚀 Features

- Detect openvpn exit during initialization- ([42a64a5](https://github.com/sinspired/VpngateClient/commit/42a64a566e1d5d3f4b8019f29b1b9bdeb5001e7f))



### 🐛 Bug Fixes

- Download vpn list over secure connection- ([dd83283](https://github.com/sinspired/VpngateClient/commit/dd8328378bcf0d76e69da7124ff0c4421f155d08))



### ⚙️ Miscellaneous Tasks

- *(init)* Fork now and continue develop,v0.0.0- ([9067a7e](https://github.com/sinspired/VpngateClient/commit/9067a7ebb99b8a1577d00ef1cb7b58cde39cf450))



## New Contributors
* @sinspired made their first contribution
* @sjakthol made their first contribution
* @rudissaar made their first contribution
<!-- generated by git-cliff -->
