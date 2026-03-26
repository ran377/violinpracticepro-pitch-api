from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
import numpy as np
import librosa

app = FastAPI(title="Violin Practice Pro Pitch API")

# 允许你的 GitHub Pages 前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ran377.github.io",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def hz_to_midi(freq: float) -> float:
    return 69 + 12 * np.log2(freq / 440.0)


def midi_to_note_name(midi_num: float) -> str:
    midi_num = int(round(midi_num))
    name = NOTE_NAMES[midi_num % 12]
    octave = midi_num // 12 - 1
    return f"{name}{octave}"


def cents_off(freq: float):
    midi_val = hz_to_midi(freq)
    nearest = np.round(midi_val)
    cents = (midi_val - nearest) * 100
    return float(cents), midi_to_note_name(nearest)


@app.get("/")
def root():
    return {"message": "Pitch API is running"}


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    suffix = os.path.splitext(file.filename)[-1] or ".wav"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        # 统一单声道读取
        y, sr = librosa.load(tmp_path, sr=22050, mono=True)

        # 去掉太安静的部分
        if len(y) == 0 or np.max(np.abs(y)) < 1e-4:
            return {
                "ok": False,
                "message": "音频太短或几乎没有有效声音"
            }

        # pYIN 音高检测：小提琴音域先粗设为 G3~E7
        f0, voiced_flag, voiced_prob = librosa.pyin(
            y,
            fmin=librosa.note_to_hz("G3"),
            fmax=librosa.note_to_hz("E7"),
            sr=sr,
            frame_length=2048,
            hop_length=256
        )

        voiced_f0 = f0[~np.isnan(f0)]

        if len(voiced_f0) == 0:
            return {
                "ok": False,
                "message": "没有检测到稳定音高，请上传更清晰的单音或单旋律片段"
            }

        # 逐帧算偏差（相对最近平均律音名）
        cents_list = []
        note_list = []

        for freq in voiced_f0:
            cents, note_name = cents_off(freq)
            cents_list.append(cents)
            note_list.append(note_name)

        cents_arr = np.array(cents_list)

        mean_abs_cents = float(np.mean(np.abs(cents_arr)))
        median_abs_cents = float(np.median(np.abs(cents_arr)))
        max_abs_cents = float(np.max(np.abs(cents_arr)))

        # 简单评级
        if mean_abs_cents <= 10:
            rating = "优秀"
        elif mean_abs_cents <= 20:
            rating = "较好"
        elif mean_abs_cents <= 35:
            rating = "一般"
        else:
            rating = "需加强"

        # 偏高 / 偏低判断
        mean_signed = float(np.mean(cents_arr))
        if mean_signed > 8:
            tendency = "整体偏高"
        elif mean_signed < -8:
            tendency = "整体偏低"
        else:
            tendency = "整体基本居中"

        # 取最常出现的几个目标音名
        unique_notes, counts = np.unique(note_list, return_counts=True)
        top_idx = np.argsort(counts)[::-1][:5]
        top_notes = [
            {"note": str(unique_notes[i]), "count": int(counts[i])}
            for i in top_idx
        ]

        return {
            "ok": True,
            "summary": {
                "rating": rating,
                "tendency": tendency,
                "mean_abs_cents": round(mean_abs_cents, 2),
                "median_abs_cents": round(median_abs_cents, 2),
                "max_abs_cents": round(max_abs_cents, 2),
                "voiced_frames": int(len(voiced_f0))
            },
            "top_notes": top_notes,
            "advice": [
                "建议先上传单音长弓或单旋律片段，第一版识别会更稳定。",
                "若整体偏高，练习时可放慢弓速并注意左手按弦落点。",
                "若整体偏低，优先检查按弦是否到位、指尖是否压实。"
            ]
        }

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
