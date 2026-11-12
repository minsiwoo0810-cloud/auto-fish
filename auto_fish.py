"""
로블록스 오토 낚시 v2 (외부 프로그램, 화면 인식 방식)
단계: 1) 차징(마우스 꾹)  2) "당기기" 버튼 클릭 반복  3) 마지막 게이지(스페이스 꾹으로 캡슐을 초록 마름모에 맞춤)

설치: pip install mss numpy opencv-python pynput
실행: python auto_fish.py   (게임 화면이 주 모니터에 보이게)
키:   F6 = 시작/정지,  F7 = 종료 (창의 버튼으로도 가능)
"""
import base64
import sys
import time

import cv2
import mss
import numpy as np
from pynput import keyboard, mouse

if sys.platform == "win32":  # 화면 배율(DPI) 때문에 클릭 좌표가 어긋나는 것 방지
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass

# ================= 설정 =================
CHARGE_TIME = 1.2        # 1단계: 마우스를 꾹 누르는 시간(초) - 게이지가 원하는 세기가 되도록 조절
BITE_TIMEOUT = 45        # 캐스팅 후 이 시간 동안 당기기 버튼이 안 뜨면 다시 캐스팅(초)
AFTER_DELAY = 2.5        # 낚시 끝난 뒤 다음 캐스팅까지 대기(초)

PULL_THRESHOLD = 0.62    # 당기기 버튼 인식 민감도(0~1), 인식이 안 되면 낮추기
PULL_SCALES = [0.6, 0.8, 1.0, 1.25, 1.5, 1.8]   # 화면 해상도에 따른 크기 차이 대응
PULL_COOLDOWN = 0.35     # 클릭 후 중복 클릭 방지 대기(초)

GREEN = (130, 210, 140)  # 3단계 초록 마름모 색
WHITE = (210, 212, 216)  # 3단계 캡슐 색
COLOR_TOL = 16           # 색 허용 오차
DEADBAND = 3             # 목표와 이 픽셀 이내면 상태 유지
LEAD = 0.10              # 속도 예측 보정(초), 캡슐이 목표를 지나치면 올리기
END_LOST_SEC = 1.3       # 마름모가 이 시간 이상 안 보이면 3단계 종료로 판단
# ========================================

TEMPLATE_B64 = "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"

kb = keyboard.Controller()
ms = mouse.Controller()
state = {"running": False, "quit": False}
hold_dir = {"v": None}   # 스페이스를 누르면 캡슐이 오른쪽(+1)/왼쪽(-1)으로 가는지 (자동 학습)


LOG_CB = {"f": None}


def log(*a):
    msg = time.strftime("%H:%M:%S") + " " + " ".join(str(x) for x in a)
    try:
        print(msg, flush=True)
    except Exception:
        pass
    if LOG_CB["f"]:
        LOG_CB["f"](msg)


def active():
    return state["running"] and not state["quit"]


def load_template():
    buf = np.frombuffer(base64.b64decode(TEMPLATE_B64), np.uint8)
    img = cv2.imdecode(buf, cv2.IMREAD_GRAYSCALE)
    return img


TPL = load_template()


def grab(sct, mon, box=None):
    """box=(x1,y1,x2,y2) 모니터 기준 좌표. RGB 배열 반환."""
    if box is None:
        region = mon
        x0, y0 = 0, 0
    else:
        x1, y1, x2, y2 = box
        region = {"left": mon["left"] + x1, "top": mon["top"] + y1,
                  "width": max(1, x2 - x1), "height": max(1, y2 - y1)}
        x0, y0 = x1, y1
    img = np.array(sct.grab(region))[:, :, :3][:, :, ::-1]  # BGRA -> RGB
    return img, x0, y0


def color_mask(img, color, tol=COLOR_TOL):
    a = img.astype(np.int16)
    return ((np.abs(a[:, :, 0] - color[0]) <= tol) &
            (np.abs(a[:, :, 1] - color[1]) <= tol) &
            (np.abs(a[:, :, 2] - color[2]) <= tol))


# ---------- 1단계: 차징 ----------
def do_cast():
    log("1단계: 차징 시작")
    ms.press(mouse.Button.left)
    t = time.time()
    while time.time() - t < CHARGE_TIME and active():
        time.sleep(0.02)
    ms.release(mouse.Button.left)


# ---------- 2단계: 당기기 버튼 ----------
def find_pull(frame_rgb):
    gray = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2GRAY)
    best = (0.0, None)
    for s in PULL_SCALES:
        tpl = cv2.resize(TPL, None, fx=s, fy=s, interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
        if tpl.shape[0] >= gray.shape[0] or tpl.shape[1] >= gray.shape[1]:
            continue
        res = cv2.matchTemplate(gray, tpl, cv2.TM_CCOEFF_NORMED)
        _, mx, _, loc = cv2.minMaxLoc(res)
        if mx > best[0]:
            # 템플릿 중심에서 마름모 중심으로 보정(-4,-5 픽셀 × 배율)
            best = (mx, (int(loc[0] + tpl.shape[1] // 2 - 4 * s), int(loc[1] + tpl.shape[0] // 2 - 5 * s)))
    if best[0] >= PULL_THRESHOLD:
        return best[1], best[0]
    return None, best[0]


def click_at(mon, x, y):
    ms.position = (mon["left"] + x, mon["top"] + y)
    time.sleep(0.04)
    ms.press(mouse.Button.left)
    time.sleep(0.05)
    ms.release(mouse.Button.left)


# ---------- 3단계: 마지막 게이지 ----------
def find_green(img):
    m = color_mask(img, GREEN)
    ys, xs = np.nonzero(m)
    if len(xs) < 12:
        return None
    w, h = xs.max() - xs.min() + 1, ys.max() - ys.min() + 1
    if len(xs) / (w * h) < 0.3 or w > 80:  # 흩어진 초록색(배경)은 무시, 마름모처럼 뭉친 것만 인정
        return None
    return float(xs.mean()), int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())


def is_final(img):
    g = find_green(img)
    if g is None:
        return False
    H = max(6, g[2] - g[1])
    return find_capsule(img, int(g[2] + 2), int(g[2] + 4.5 * H), max(5, int(H * 0.9))) is not None


def find_capsule(img, top, bottom, need_h):
    band = color_mask(img[top:bottom], WHITE)
    cols = band.sum(axis=0)
    idx = np.nonzero(cols >= need_h)[0]
    if len(idx) == 0:
        return None
    # 연속된 열 묶음 중 가장 넓은 것 선택
    groups = np.split(idx, np.nonzero(np.diff(idx) > 2)[0] + 1)
    g = max(groups, key=len)
    return float(g.mean())


def set_hold(held):
    if held:
        kb.press(keyboard.Key.space)
    else:
        kb.release(keyboard.Key.space)


def do_final(sct, mon):
    log("3단계: 마지막 게이지 시작")
    held = False
    lost_since = None
    prev_cx, prev_t = None, None
    box = None
    samples = {True: [], False: []}
    t_start = time.time()
    probe_phase = hold_dir["v"] is None  # 방향을 아직 모르면 처음에 번갈아 눌러서 학습
    try:
        while active():
            frame, ox, oy = grab(sct, mon, box)
            g = find_green(frame)
            if g is None and box is not None:
                box = None
                continue
            now = time.perf_counter()
            if g is None:
                if lost_since is None:
                    lost_since = time.time()
                elif time.time() - lost_since > END_LOST_SEC:
                    break
                time.sleep(0.02)
                continue
            lost_since = None
            gx, gy0, gy1, _, _ = g
            H = max(6, gy1 - gy0)
            tx = gx + ox
            top = int(gy1 + 2)
            bottom = int(gy1 + 4.5 * H)
            if box is None:  # 이후에는 게이지 주변 가로 띠만 캡처해서 빠르게
                box = (0, max(0, int(oy + gy0 - 3 * H)), mon["width"], min(mon["height"], int(oy + gy1 + 6 * H)))
                continue
            cx = find_capsule(frame, top, bottom, max(5, int(H * 0.9)))
            if cx is None:
                continue
            cx += ox

            vel = 0.0
            if prev_cx is not None and now > prev_t:
                dx = cx - prev_cx
                vel = dx / (now - prev_t)
                if probe_phase or hold_dir["v"] is None:
                    samples[held].append(dx)
            prev_cx, prev_t = cx, now

            # 방향 학습
            if hold_dir["v"] is None and len(samples[True]) >= 6 and len(samples[False]) >= 6:
                diff = np.mean(samples[True]) - np.mean(samples[False])
                if abs(diff) >= 0.4:
                    hold_dir["v"] = 1 if diff > 0 else -1
                    log("방향 학습 완료:", "스페이스=오른쪽" if hold_dir["v"] > 0 else "스페이스=왼쪽")
                    probe_phase = False
                elif time.time() - t_start > 3:
                    hold_dir["v"] = 1
                    probe_phase = False

            if hold_dir["v"] is None:
                want = int((time.time() - t_start) / 0.25) % 2 == 0  # 0.25초 간격으로 번갈아
            else:
                err = (tx - cx) - LEAD * vel
                signed = err * hold_dir["v"]
                if signed > DEADBAND:
                    want = True
                elif signed < -DEADBAND:
                    want = False
                else:
                    want = held
            if want != held:
                set_hold(want)
                held = want
            time.sleep(0.005)
    finally:
        set_hold(False)
    log("3단계 종료")


# ---------- 메인 루프 ----------
def main_loop():
    with mss.mss() as sct:
        mon = sct.monitors[1]
        last_cast = 0.0
        last_pull = 0.0
        need_cast = True
        pulls = 0
        while not state["quit"]:
            if not state["running"]:
                time.sleep(0.1)
                continue
            frame, _, _ = grab(sct, mon)

            # 3단계(초록 마름모) 우선 확인
            if is_final(frame):
                do_final(sct, mon)
                need_cast = True
                pulls = 0
                time.sleep(AFTER_DELAY)
                continue

            # 2단계(당기기 버튼)
            if time.time() - last_pull > PULL_COOLDOWN:
                pos, score = find_pull(frame)
                if pos is not None:
                    click_at(mon, pos[0], pos[1])
                    pulls += 1
                    last_pull = time.time()
                    last_cast = time.time()  # 당기는 중에는 재캐스팅 타이머 리셋
                    need_cast = False
                    log(f"2단계: 당기기 클릭 #{pulls} (일치도 {score:.2f})")
                    continue

            # 1단계(캐스팅)
            if need_cast or time.time() - last_cast > BITE_TIMEOUT:
                if need_cast and last_cast and time.time() - last_cast < AFTER_DELAY:
                    time.sleep(0.1)
                    continue
                do_cast()
                last_cast = time.time()
                need_cast = False
                continue
            time.sleep(0.05)


def run_gui():
    import threading
    import tkinter as tk

    root = tk.Tk()
    root.title("로블록스 오토 낚시")
    root.geometry("430x440")
    root.attributes("-topmost", True)

    status = tk.StringVar(value="정지됨")
    tk.Label(root, textvariable=status, font=("맑은 고딕", 14, "bold")).pack(pady=(10, 4))
    btn = tk.Button(root, text="시작 (F6)", width=20, height=2, bg="#4caf50", fg="white")
    btn.pack(pady=4)

    frm = tk.LabelFrame(root, text="설정")
    frm.pack(fill="x", padx=12, pady=6)
    entries = {}
    for row, (label, key) in enumerate([("차징 시간(초)", "CHARGE_TIME"),
                                        ("당기기 인식 민감도(0~1)", "PULL_THRESHOLD"),
                                        ("재캐스팅 대기(초)", "BITE_TIMEOUT")]):
        tk.Label(frm, text=label).grid(row=row, column=0, sticky="w", padx=6, pady=2)
        e = tk.Entry(frm, width=8)
        e.insert(0, str(globals()[key]))
        e.grid(row=row, column=1, padx=6)
        entries[key] = e

    box = tk.Text(root, height=12, state="disabled", font=("Consolas", 9))
    box.pack(fill="both", expand=True, padx=12, pady=(0, 10))

    def append(msg):
        box.config(state="normal")
        box.insert("end", msg + "\n")
        box.see("end")
        box.config(state="disabled")

    LOG_CB["f"] = lambda m: root.after(0, append, m)

    def apply_settings():
        for key, e in entries.items():
            try:
                globals()[key] = float(e.get())
            except ValueError:
                pass

    def really_start():
        apply_settings()
        state["running"] = True
        status.set("작동 중")
        btn.config(text="정지 (F6)", bg="#e53935")
        log("시작")

    def stop():
        state["running"] = False
        set_hold(False)
        try:
            ms.release(mouse.Button.left)
        except Exception:
            pass
        status.set("정지됨")
        btn.config(text="시작 (F6)", bg="#4caf50")
        log("정지")

    def toggle():
        if state["running"]:
            stop()
        else:
            status.set("3초 뒤 시작 - 로블록스 화면을 클릭하세요")
            root.after(3000, really_start)

    def close():
        state["quit"] = True
        set_hold(False)
        root.destroy()

    btn.config(command=toggle)
    root.protocol("WM_DELETE_WINDOW", close)

    def hotkey(key):
        if key == keyboard.Key.f6:
            root.after(0, toggle)
        elif key == keyboard.Key.f7:
            root.after(0, close)

    keyboard.Listener(on_press=hotkey, daemon=True).start()
    threading.Thread(target=main_loop, daemon=True).start()
    log("준비 완료. F6 = 시작/정지, F7 = 종료")
    root.mainloop()


if __name__ == "__main__":
    run_gui()
