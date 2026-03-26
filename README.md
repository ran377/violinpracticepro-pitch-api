# Violin Practice Pro Pitch API

一个用于小提琴网页 Demo 的后端接口，提供基础的音准检测功能。

## 功能
- 接收用户上传的音频文件
- 使用 `librosa.pyin` 做基础频率（F0）检测
- 输出整体音准评级、偏高/偏低趋势、平均偏差、常见音名与基础练习建议

## 仓库结构

```text
.
├── main.py
├── requirements.txt
├── render.yaml
├── .gitignore
└── README.md
```

## 本地运行

1. 创建虚拟环境并安装依赖：

```bash
pip install -r requirements.txt
```

2. 启动服务：

```bash
uvicorn main:app --reload
```

3. 打开：

- 接口主页：`http://127.0.0.1:8000`
- 接口文档：`http://127.0.0.1:8000/docs`

## 接口说明

### `GET /`
健康检查接口。

### `POST /analyze`
上传音频文件并返回分析结果。

表单字段：
- `file`: 音频文件

返回示例：

```json
{
  "ok": true,
  "summary": {
    "rating": "较好",
    "tendency": "整体基本居中",
    "mean_abs_cents": 12.54,
    "median_abs_cents": 9.31,
    "max_abs_cents": 43.27,
    "voiced_frames": 188
  },
  "top_notes": [
    {"note": "A4", "count": 52},
    {"note": "E5", "count": 40}
  ],
  "advice": [
    "建议先上传单音长弓或单旋律片段，第一版识别会更稳定。"
  ]
}
```

## 部署到 Render

1. 把这些文件上传到一个新的 GitHub 仓库
2. 登录 Render
3. 选择 **New +** → **Blueprint** 或 **Web Service**
4. 连接 GitHub 仓库
5. 如果识别 `render.yaml`，可直接部署
6. 部署完成后会得到一个公开 API 地址，例如：

```text
https://violinpracticepro-pitch-api.onrender.com
```

## 前端跨域说明

当前 `main.py` 已允许以下来源访问：
- `https://ran377.github.io`
- `http://127.0.0.1:5500`
- `http://localhost:5500`

如果以后你换了域名，请同步修改 `allow_origins`。
