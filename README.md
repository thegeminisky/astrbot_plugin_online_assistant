# AstrBot插件 - 小助手太一

太一，您的私人小秘，提供多种实用小功能。

## 📚目录结构
```text
│  .gitignore             #git文件管理
│  LICENSE                #项目license
│  logo.png               #插件图标
│  main.py                #插件主程序
│  metadata.yaml          #插件市场信息
│  README.md              #插件README
│  requirements.txt       #插件依赖
│  _conf_schema.json      #插件配置文件
```

## 🚀 功能特点
| 功能         | 描述            |
|------------|---------------|
| 🌐 未读邮件速查  | 查询所有支持SMAP的邮箱 |
| ☁️ 格点气象查询  | 支持自定义地点的km级降雨查询 |
| 🔒 完善的访问控制 | 仅全局管理员可使用命令   |
| 📊 LLM余额查询 | 查询硅基流动账户余额    |
| 📺 查询环球新闻  | 获取每天60秒读懂世界   |
| 🛡️ 模块互相独立 | 各模块可独立运行      |
| 🧷 反卡片解析   | 从QQ卡片中提取直链    |

## 📦安装与使用指南

### 1. 经插件市场安装后在插件配置中完成配置
#### 各模块独立运行，完善所需模块的配置即可
```text
钉钉自定义机器人API:预留接口，暂无实际用途
    钉钉机器人access_token获取
    https://open.dingtalk.com/document/orgapp/obtain-the-webhook-address-of-a-custom-robot
    钉钉机器人secret获取
    https://open.dingtalk.com/document/robots/customize-robot-security-settings
LLM服务商余额查询:
    服务商1 名称:硅基流动
    服务商1 APIKEY:sk-xxxxxxx
和风天气API:
    和风天气私钥:将依照和风天气JWT身份认证生成的ed25519-private.pem文件以记事本形式打开，在此处粘贴全部内容
    和风天气api_host:https://dev.qweather.com/docs/configuration/api-host/
    和风天气kid:https://dev.qweather.com/docs/configuration/authentication/
    和风天气sub:https://dev.qweather.com/docs/configuration/authentication/
    天气监测点坐标经纬度:经度在前纬度在后，英文逗号分隔，十进制格式，北纬东经为正，南纬西经为负。例：116.41,39.95
邮箱SMTP信息:
    参阅对应邮箱指导文档
每天60秒读懂世界公共实例Host:
    news_host:该链接中的公共实例Hosthttps://docs.60s-api.viki.moe/7306811m0
```
### 1.1 命令说明
| 命令    | 是否是管理员命令 | 描述                |
|-------|----------|-------------------|
| 助手 邮箱 | 是        | 通过SMAP查询未读邮件数量    |
| 助手 天气 | 是        | 查询自定义地点未来24小时降雨与否 |
| 助手 余额 | 是        | 查询自定义APIKEY的账户余额  |
| 助手 新闻 | 是        | 获取每天60秒读懂世界新闻速报   |
### 2. 从源码开始配置

### 2.1 环境要求
- Python 3.10+
- 依赖库：
```bash
pip install requests pyjwt pytz
```
### 2.2 填写配置文件_conf_schema.json
配置要求同上

### 2.3 导入Astrbot运行

## 安全建议
**🔒保护服务密钥🔒**
- ⚠️确保_conf_schema.json存储在安全位置
- ⚠️将_conf_schema.json添加入.gitignore⚠
- ⚠️生产环境建议使用安全的密钥存储服务

## 许可证
本项目采用 **GPL-3.0 许可证** - 详细信息请参阅LICENSE文件。

## 贡献指南
欢迎通过Issues提交问题反馈，或通过Pull Request贡献代码。
如有任何使用问题，请创建Issue或联系项目维护者。