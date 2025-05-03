# 📝 Changelog

Latest changes to this project.


### [1.2.0] - 2025-05-03



### 🚀 Features

- 自动根据平台设置tmp,cache,config文件夹- ([0714fd3](https://github.com/sinspired/VpngateClient/commit/0714fd3a8c24aae1a62a8ea0c7cf723e3e072e8b))
- 添加节点延迟检测和排序- ([6e743d0](https://github.com/sinspired/VpngateClient/commit/6e743d0b9abf4fa9111942d293b0322ce2ce26ab))



### 🐛 Bug Fixes

- 修复模块导入和setup- ([19038d7](https://github.com/sinspired/VpngateClient/commit/19038d7b149c8e7ec282acce47595efcd7da217d))
- 修复windows平台无法使用select进行倒计时的错误- ([7dd3ea0](https://github.com/sinspired/VpngateClient/commit/7dd3ea0ea06877e52053a8bf7aeb3de5a003ed09))
- Pyinstaller在根目录下运行时，需要指定导入模块所在路径- ([6468245](https://github.com/sinspired/VpngateClient/commit/6468245b63d9a00b146053c9f1c7d40249735b20))



### 📚 Documentation

- *(README.md)* 更新使用说明- ([9f8b723](https://github.com/sinspired/VpngateClient/commit/9f8b723a75edc3428995093b74bb741730375aa8))



### ⚡ Performance

- 优化运行时界面输出- ([754e176](https://github.com/sinspired/VpngateClient/commit/754e176e56ec6cfd65e27ccc0b07acc6e19b669e))



### ⚙️ Miscellaneous Tasks

- *(release)* 修改发布流程- ([ef6da02](https://github.com/sinspired/VpngateClient/commit/ef6da0265984c22f17987a2727b9e78889b25584))
- *(release)* Bump version to 1.2.0- ([511c7fd](https://github.com/sinspired/VpngateClient/commit/511c7fd431ce427a06bcdd66358f00b2f3229ad8))




### [1.1.0] - 2025-05-03



### 🚀 Features

- 添加连接状态监控，自动切换，自动收藏优质配置等功能- ([7dfe7b5](https://github.com/sinspired/VpngateClient/commit/7dfe7b5aae3aa4590548e516934b5c18b7f43aa4))



>1. 自动显示下载数据量，显示上行下行速率；



>2. 正常连接一段时间的配置,会自动保存收藏;



>3. 优先连接收藏的配置。



### ⚙️ Miscellaneous Tasks

- *(release)* Creat_release.yml，deb包申请sudo权限- ([c713e5a](https://github.com/sinspired/VpngateClient/commit/c713e5a3dc156c2891d3b8371c17560bf8edff37))




### [1.0.1] - 2025-05-03



### 🐛 Bug Fixes

- 跨平台编译- ([5533cbb](https://github.com/sinspired/VpngateClient/commit/5533cbbf010a8f0e8abd791db0298c897dcf16c9))
- 解决跨平台编译冲突，移除console导入- ([1053228](https://github.com/sinspired/VpngateClient/commit/10532283e7813811eeadaef9ae94f4bece99604a))




### [1.0.0] - 2025-05-03



### 🚀 Features

- For Windows & bug fix & add new feature- ([ae0ea0c](https://github.com/sinspired/VpngateClient/commit/ae0ea0cd0011775d36b1f6805189103ed2feab83))
- 1.add status monitor;2.add connection speedtest- ([7d3f092](https://github.com/sinspired/VpngateClient/commit/7d3f09298a02cfc7436cd56fa94a5cb574dd84ad))
- Add clean status tempfile,add timeout in speedtest function- ([ddc73a7](https://github.com/sinspired/VpngateClient/commit/ddc73a7069026fd065acd04267d0f8b69b5dc6c8))
- Add new api url- ([cdd3367](https://github.com/sinspired/VpngateClient/commit/cdd3367198dee260c823e3765f0af95e82905ed1))
- 添加更多GitHub代理网址- ([59cbb8c](https://github.com/sinspired/VpngateClient/commit/59cbb8c1f9d89cb0bca546046a03179b0ff0389e))



### 🐛 Bug Fixes

- Serverlist download- ([e673274](https://github.com/sinspired/VpngateClient/commit/e67327465394ae6199945fbbcf4e697c7fe4831f))
- 修复github proxy网址- ([0173b35](https://github.com/sinspired/VpngateClient/commit/0173b351b430bb7dc3a750471d4ef72e4820e1b2))



### ⚙️ Miscellaneous Tasks

- *(release)* Creat release action- ([fc7c081](https://github.com/sinspired/VpngateClient/commit/fc7c0811d87590a83fce2ea325273406393a5235))
- *(config)* Modifiy default min download speed- ([c4e86fb](https://github.com/sinspired/VpngateClient/commit/c4e86fb833c4dea4a54fd4bf27eaf16b4f5b9736))
- Add VpngateClient_global.py- ([e7460c8](https://github.com/sinspired/VpngateClient/commit/e7460c88808352ef49bce24e1f21f7512ab927cb))
- Add more translation- ([d5de135](https://github.com/sinspired/VpngateClient/commit/d5de135108f1637196d5468259c62e8ae43f6a18))
- Add more translation- ([7599092](https://github.com/sinspired/VpngateClient/commit/75990928ed6bc7d08c3e6919cd6a4304422570dc))
- Add more translation- ([c90c405](https://github.com/sinspired/VpngateClient/commit/c90c405e2c4e8a7a07d6ec3c7070cbe66a03c86b))
- 添加logo文件- ([6b9a444](https://github.com/sinspired/VpngateClient/commit/6b9a44404df7bdd4fa4cd532495ae9d6cd2bfb42))
- 清理文件- ([5c1e51e](https://github.com/sinspired/VpngateClient/commit/5c1e51ef058320c85f9c3d6c6fae4b5f312e685e))
- 清理文件- ([a37ba22](https://github.com/sinspired/VpngateClient/commit/a37ba224196dba049254d5a23f02c4143ede4970))




### [0.0.0] - 2025-05-03



### 🚀 Features

- Detect openvpn exit during initialization- ([42a64a5](https://github.com/sinspired/VpngateClient/commit/42a64a566e1d5d3f4b8019f29b1b9bdeb5001e7f))



### 🐛 Bug Fixes

- Download vpn list over secure connection- ([dd83283](https://github.com/sinspired/VpngateClient/commit/dd8328378bcf0d76e69da7124ff0c4421f155d08))



### ⚙️ Miscellaneous Tasks

- *(init)* Fork now and continue develop,v0.0.0- ([9067a7e](https://github.com/sinspired/VpngateClient/commit/9067a7ebb99b8a1577d00ef1cb7b58cde39cf450))



## New Contributors
* @sjakthol made their first contribution
* @rudissaar made their first contribution
<!-- generated by git-cliff -->
