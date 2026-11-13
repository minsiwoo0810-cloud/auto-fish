"""
AutoFish v3 - 로블록스 자동 낚시 (화면 인식 방식, 외부 프로그램)

단계  1) 차징(마우스 꾹)  2) "당기기" 버튼 클릭 반복  3) 마지막 게이지(스페이스로 캡슐을 초록 마름모에 맞춤)
키    F6 = 시작/정지,  F7 = 종료
의존  mss numpy opencv-python pynput  (tkinter는 파이썬 기본 포함)
"""
import base64
import json
import os
import queue
import random
import sys
import threading
import time
import traceback
from collections import deque

import cv2
import mss
import numpy as np
from pynput import keyboard, mouse

if sys.platform == "win32":  # 화면 배율(DPI)로 클릭 좌표가 어긋나는 것 방지
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass

APP_NAME = "AutoFish"
TEMPLATE_B64 = "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"

DEFAULTS = {
    "charge_time": 1.2,     # 1단계 차징 시간(초)
    "bite_timeout": 45.0,   # 캐스팅 후 버튼이 안 뜨면 재캐스팅(초)
    "after_delay": 2.5,     # 낚시 끝난 뒤 다음 캐스팅까지(초)
    "pull_sens": 0.55,      # 당기기 버튼 인식 기준(낮을수록 관대)
    "lead": 0.10,           # 게이지 예측 보정(초)
    "monitor": 1,           # 캡처할 모니터 번호
    "topmost": True,        # 항상 위
}

# ---- 색상 (RGB 기준 값을 BGR로 변환해 사용) ----
GREEN_BGR = (140, 210, 130)   # 초록 마름모 (130,210,140)
DARK_BGR = (35, 30, 26)       # 당기기 버튼 안쪽 (26,30,35)
DIAMOND_REF_W = 90.0          # 템플릿을 자른 원본에서의 마름모 안쪽(어두운 부분) 너비
END_LOST_SEC = 1.3            # 초록 마름모가 이 시간 이상 안 보이면 3단계 종료


# =====================================================================
#  설정 저장/불러오기
# =====================================================================
def data_dir():
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    d = os.path.join(base, APP_NAME)
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    return d


def load_settings():
    cfg = dict(DEFAULTS)
    try:
        with open(os.path.join(data_dir(), "settings.json"), "r", encoding="utf-8") as f:
            saved = json.load(f)
        for k in DEFAULTS:
            if k in saved and type(saved[k]) == type(DEFAULTS[k]):
                cfg[k] = saved[k]
            elif k in saved and isinstance(DEFAULTS[k], float) and isinstance(saved[k], int):
                cfg[k] = float(saved[k])
    except Exception:
        pass
    return cfg


def save_settings(cfg):
    try:
        with open(os.path.join(data_dir(), "settings.json"), "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# =====================================================================
#  화면 인식
# =====================================================================
def _range(frame, bgr, tol):
    lo = tuple(max(0, c - tol) for c in bgr) + (0,)
    hi = tuple(min(255, c + tol) for c in bgr) + (255,)
    return cv2.inRange(frame, lo, hi)


def find_green(frame, tol=22):
    """3단계 초록 마름모. 반환: dict(x, top, bottom, h) 또는 None"""
    m = _range(frame, GREEN_BGR, tol)
    pts = cv2.findNonZero(m)
    if pts is None or len(pts) < 10:
        return None
    x, y, w, h = cv2.boundingRect(pts)
    if len(pts) / float(w * h) < 0.3 or w > max(60, frame.shape[1] * 0.08):
        return None  # 흩어진 초록색(배경)은 무시
    return {"x": x + w / 2.0, "top": y, "bottom": y + h - 1, "h": h}


def find_capsule(frame, g):
    """초록 마름모 아래 게이지 바 위의 흰 캡슐 x좌표."""
    H = max(6, g["h"])
    top = g["bottom"] + 2
    bot = min(frame.shape[0], int(g["bottom"] + 5 * H))
    if bot - top < 4:
        return None
    m = cv2.inRange(frame[top:bot], (180, 180, 180, 0), (255, 255, 255, 255))
    cols = np.count_nonzero(m, axis=0)
    idx = np.flatnonzero(cols >= max(6, H))
    if idx.size == 0:
        return None
    groups = np.split(idx, np.flatnonzero(np.diff(idx) > 2) + 1)
    groups = [gp for gp in groups if len(gp) <= max(40, H * 3)]
    if not groups:
        return None
    return float(max(groups, key=len).mean())


def is_final(frame):
    g = find_green(frame)
    if g is None:
        return None
    return g if find_capsule(frame, g) is not None else None


def _diamond_stats(frame, x, y, w, h):
    """어두운 덩어리(x,y,w,h)가 '흰 테두리 + 흰 글자' 마름모인지 수치로 확인."""
    Hh, Ww = frame.shape[:2]
    pad = int(0.25 * w)
    x0, y0 = max(0, x - pad), max(0, y - pad)
    x1, y1 = min(Ww, x + w + pad), min(Hh, y + h + pad)
    crop = frame[y0:y1, x0:x1]
    white = cv2.inRange(crop, (165, 165, 165, 0), (255, 255, 255, 255)) > 0
    hh, ww = white.shape
    yy, xx = np.mgrid[0:hh, 0:ww]
    metric = np.abs(xx - (x + w / 2.0 - x0)) / (w / 2.0) + np.abs(yy - (y + h / 2.0 - y0)) / (h / 2.0)
    text = white[metric < 0.75]
    t_ratio = float(text.mean()) if text.size else 0.0
    r_ratio = 0.0  # 흰 테두리: 마름모 윤곽선을 따라 얇게 이어진 흰 띠(가장 흰 구간의 비율)
    for lo in np.arange(1.0, 1.45, 0.03):
        sel = white[(metric >= lo) & (metric < lo + 0.06)]
        if sel.size:
            r_ratio = max(r_ratio, float(sel.mean()))
    return t_ratio, r_ratio, crop


def template_score(crop, tpl, w):
    """crop을 원본 배율로 맞춘 뒤 '당기기' 글자 템플릿과 비교."""
    s = DIAMOND_REF_W / float(w)
    g = cv2.cvtColor(crop, cv2.COLOR_BGRA2GRAY)
    g = cv2.resize(g, None, fx=s, fy=s, interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    if g.shape[0] < tpl.shape[0] or g.shape[1] < tpl.shape[1]:
        return 0.0
    res = cv2.matchTemplate(g, tpl, cv2.TM_CCOEFF_NORMED)
    return float(cv2.minMaxLoc(res)[1])


def find_pull(frame, tpl, sens):
    """당기기 버튼(어두운 마름모). 반환: (cx, cy, score) 또는 None.
    1) 어두운 마름모꼴 덩어리 후보 찾기(빠름, 해상도 무관)  2) 흰 테두리/글자/템플릿으로 확인"""
    Hh, Ww = frame.shape[:2]
    m = _range(frame, DARK_BGR, 20)
    n, _, st, _ = cv2.connectedComponentsWithStats(m, connectivity=4)
    cands = []
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if w < 24 or h < 24 or w > Ww * 0.5 or h > Hh * 0.7:
            continue
        if not (0.8 <= w / float(h) <= 1.25):
            continue
        if not (0.30 <= a / float(w * h) <= 0.56):
            continue
        cands.append((int(a), int(x), int(y), int(w), int(h)))
    cands.sort(reverse=True)
    best = None
    for a, x, y, w, h in cands[:6]:
        t_ratio, r_ratio, crop = _diamond_stats(frame, x, y, w, h)
        if r_ratio < 0.35 or t_ratio < 0.01 or t_ratio > 0.40:
            continue
        sc = template_score(crop, tpl, w)
        ok = sc >= sens or (r_ratio >= 0.6 and 0.03 <= t_ratio <= 0.30)
        if ok:
            score = max(sc, r_ratio)
            if best is None or score > best[2]:
                best = (x + w / 2.0, y + h / 2.0, score)
    return best


def find_pull_template(frame, tpl, sens):
    """보조 방법: 템플릿 다중 배율 매칭(느리므로 가끔만)."""
    small = cv2.resize(frame, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_BGRA2GRAY)
    best = (0.0, None)
    for s in (0.4, 0.55, 0.75, 1.0, 1.3):
        t = cv2.resize(tpl, None, fx=s, fy=s, interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
        if t.shape[0] >= gray.shape[0] or t.shape[1] >= gray.shape[1] or t.shape[0] < 6:
            continue
        res = cv2.matchTemplate(gray, t, cv2.TM_CCOEFF_NORMED)
        _, mx, _, loc = cv2.minMaxLoc(res)
        if mx > best[0]:
            best = (mx, ((loc[0] + t.shape[1] / 2.0 - 4 * s) * 2, (loc[1] + t.shape[0] / 2.0 - 5 * s) * 2))
    if best[0] >= max(sens + 0.15, 0.7):
        return best[1][0], best[1][1], best[0]
    return None


# =====================================================================
#  3단계 제어기 (캡슐을 초록 마름모에 맞춤)
# =====================================================================
class _AB:
    """알파-베타 필터: 위치와 속도를 부드럽게 추정."""

    def __init__(self, a=0.55, b=0.12):
        self.a, self.b = a, b
        self.x, self.v, self.t = None, 0.0, None

    def step(self, t, z):
        if self.x is None:
            self.x, self.t = z, t
            return
        dt = max(1e-3, t - self.t)
        xp = self.x + self.v * dt
        r = z - xp
        self.x = xp + self.a * r
        self.v += self.b * r / dt
        self.t = t


class Controller:
    """캡슐을 초록 마름모에 맞추는 제어기.
    처음 ~1초간 스페이스를 0.25초씩 번갈아 눌러서
      (1) 어느 쪽으로 움직이는지, (2) 반응이 즉각적인지/관성이 있는지를 학습하고,
    이후에는 목표와 캡슐의 위치+속도를 예측해서 누름/뗌을 결정한다."""

    def __init__(self, lead=0.10, hold_dir=None):
        self.lead_base, self.lead = lead, lead
        self.hold_dir = hold_dir
        self.held = False
        self.t0 = None
        self.fc, self.ft = _AB(), _AB()
        self.phase = None            # dict(t, x, held, vs=[(dt, v)])
        self.phase_v = {True: [], False: []}
        self.resp = []               # 반응 속도 지표(1에 가까울수록 즉각 반응)

    def _phase_end(self, t, cx):
        ph = self.phase
        dur = t - ph["t"]
        if dur > 0.15:
            self.phase_v[ph["held"]].append((cx - ph["x"]) / dur)
        vs = ph["vs"]
        if dur > 0.2 and len(vs) > 6:
            def at(sec):
                return min(vs, key=lambda p: abs(p[0] - sec))[1]
            v0, v1, v2 = at(0.0), at(0.08), at(0.2)
            if abs(v2 - v0) > 20:
                self.resp.append(min(1.0, max(0.0, (v1 - v0) / (v2 - v0))))

    def update(self, t, tx, cx, H):
        if self.t0 is None:
            self.t0 = t
        self.fc.step(t, cx)
        self.ft.step(t, tx)

        if self.hold_dir is None:  # 방향/반응 학습
            want = int((t - self.t0) / 0.25) % 2 == 0
            if self.phase is None:
                self.phase = {"t": t, "x": cx, "held": want, "vs": []}
            self.phase["vs"].append((t - self.phase["t"], self.fc.v))
            if want != self.phase["held"]:
                self._phase_end(t, cx)
                self.phase = {"t": t, "x": cx, "held": want, "vs": []}
            sh, sr = self.phase_v[True], self.phase_v[False]
            if len(sh) >= 2 and len(sr) >= 2:
                diff = float(np.mean(sh) - np.mean(sr))
                if abs(diff) >= max(10.0, H):
                    self.hold_dir = 1 if diff > 0 else -1
            if self.hold_dir is None and t - self.t0 > 3.0:
                self.hold_dir = 1
            if self.hold_dir is not None and self.resp:
                r = float(np.mean(self.resp))      # 관성이 클수록 더 멀리 내다보고 제어
                self.lead = self.lead_base + 0.25 * (1.0 - r)
            if self.hold_dir is None:
                self.held = want
                return want

        db = max(2.0, 0.25 * H)
        err = (self.ft.x + self.ft.v * self.lead) - (self.fc.x + self.fc.v * self.lead)
        sgn = err * self.hold_dir
        if sgn > db:
            self.held = True
        elif sgn < -db:
            self.held = False
        return self.held


# =====================================================================
#  자동 낚시 엔진 (별도 스레드)
# =====================================================================
class Bot(threading.Thread):
    def __init__(self, cfg, q):
        super().__init__(daemon=True)
        self.cfg = cfg
        self.q = q
        self.running = False
        self.quit = False
        self.gui_rect = None
        self.kb = keyboard.Controller()
        self.ms = mouse.Controller()
        self.hold_dir = None
        self.stats = {"catches": 0, "pulls": 0, "casts": 0, "t0": None}
        self.tpl = cv2.imdecode(np.frombuffer(base64.b64decode(TEMPLATE_B64), np.uint8), cv2.IMREAD_GRAYSCALE)
        self._stage = ""

    # ---------- 유틸 ----------
    def log(self, msg):
        self.q.put(("log", msg))

    def stage(self, name):
        if name != self._stage:
            self._stage = name
            self.q.put(("stage", name))

    def active(self):
        return self.running and not self.quit

    def release_all(self):
        try:
            self.kb.release(keyboard.Key.space)
        except Exception:
            pass
        try:
            self.ms.release(mouse.Button.left)
        except Exception:
            pass

    def monitor(self, sct):
        idx = int(self.cfg.get("monitor", 1))
        mons = sct.monitors
        return mons[idx] if 1 <= idx < len(mons) else mons[1]

    @staticmethod
    def grab(sct, mon, box=None):
        if box is None:
            region, ox, oy = mon, 0, 0
        else:
            x1, y1, x2, y2 = box
            region = {"left": mon["left"] + x1, "top": mon["top"] + y1,
                      "width": max(1, x2 - x1), "height": max(1, y2 - y1)}
            ox, oy = x1, y1
        shot = sct.grab(region)
        return np.frombuffer(shot.raw, dtype=np.uint8).reshape(shot.height, shot.width, 4), ox, oy

    # ---------- 입력 ----------
    def cursor_to_game(self, mon):
        """마우스가 이 프로그램 창 위에 있으면 게임 화면 중앙으로 옮긴다(클릭이 앱에 먹히는 것 방지)."""
        r = self.gui_rect
        if not r:
            return
        x, y = self.ms.position
        if r[0] <= x <= r[2] and r[1] <= y <= r[3]:
            self.ms.position = (mon["left"] + mon["width"] // 2, mon["top"] + mon["height"] // 2)
            time.sleep(0.05)

    def click_at(self, mon, x, y):
        jx, jy = random.randint(-2, 2), random.randint(-2, 2)
        self.ms.position = (mon["left"] + int(x) + jx, mon["top"] + int(y) + jy)
        time.sleep(0.02)
        self.ms.press(mouse.Button.left)
        time.sleep(0.04)
        self.ms.release(mouse.Button.left)

    def cast(self, mon):
        self.stage("1단계 · 차징")
        self.cursor_to_game(mon)
        dur = max(0.1, float(self.cfg["charge_time"]) * random.uniform(0.97, 1.03))
        self.ms.press(mouse.Button.left)
        t = time.time()
        while time.time() - t < dur and self.active():
            time.sleep(0.01)
        self.ms.release(mouse.Button.left)
        self.stats["casts"] += 1
        self.log("캐스팅")

    # ---------- 3단계 ----------
    def run_final(self, sct, mon):
        self.stage("3단계 · 게이지")
        self.log("게이지 시작")
        ctl = Controller(lead=float(self.cfg["lead"]), hold_dir=self.hold_dir)
        held, lost, box = False, None, None
        t_begin = time.time()
        try:
            while self.active():
                frame, ox, oy = self.grab(sct, mon, box)
                g = find_green(frame)
                now = time.time()
                if g is None:
                    box = None  # 띠 영역에 없으면 전체 화면에서 다시 찾기
                    if lost is None:
                        lost = now
                    elif now - lost > END_LOST_SEC:
                        break
                    time.sleep(0.01)
                    continue
                lost = None
                H = max(6, g["h"])
                if box is None:  # 게이지 주변 가로 띠만 캡처해서 속도 올리기
                    box = (0, max(0, int(oy + g["top"] - 3 * H)), mon["width"],
                           min(mon["height"], int(oy + g["bottom"] + 7 * H)))
                cx = find_capsule(frame, g)
                if cx is None:
                    continue
                want = ctl.update(time.perf_counter(), ox + g["x"], ox + cx, H)
                if want != held:
                    (self.kb.press if want else self.kb.release)(keyboard.Key.space)
                    held = want
                if ctl.hold_dir is not None and self.hold_dir is None:
                    self.hold_dir = ctl.hold_dir
                    self.log("조작 방향 학습: 스페이스 = " + ("오른쪽" if ctl.hold_dir > 0 else "왼쪽"))
        finally:
            try:
                self.kb.release(keyboard.Key.space)
            except Exception:
                pass
        if time.time() - t_begin > 1.5:
            self.stats["catches"] += 1
        self.log("게이지 종료")

    # ---------- 메인 루프 ----------
    def run(self):
        try:
            self._loop()
        except Exception:
            self.log("엔진 오류: " + traceback.format_exc().splitlines()[-1])
            try:
                with open(os.path.join(data_dir(), "crash.log"), "a", encoding="utf-8") as f:
                    f.write(traceback.format_exc() + "\n")
            except Exception:
                pass

    def _loop(self):
        with mss.mss() as sct:
            phase, t_next, t_cast, t_pull = "cast", 0.0, 0.0, 0.0
            last_click = (0.0, -999, -999)
            last_tpl = 0.0
            last_det = 0.0
            while not self.quit:
                if not self.running:
                    if phase != "cast":
                        phase = "cast"
                    time.sleep(0.05)
                    self.stage("대기")
                    continue
                mon = self.monitor(sct)
                frame, _, _ = self.grab(sct, mon)
                now = time.time()

                g = is_final(frame)
                pull = None if g else find_pull(frame, self.tpl, float(self.cfg["pull_sens"]))
                if g is None and pull is None and now - last_tpl > 0.4 and phase in ("wait", "pull"):
                    last_tpl = now
                    pull = find_pull_template(frame, self.tpl, float(self.cfg["pull_sens"]))
                if now - last_det > 0.2:
                    last_det = now
                    self.q.put(("detect", pull is not None, g is not None))

                if g is not None:                       # 3단계
                    self.run_final(sct, mon)
                    phase, t_next = "cooldown", time.time() + float(self.cfg["after_delay"])
                    continue

                if pull is not None:                    # 2단계
                    px, py, sc = pull
                    same = (now - last_click[0] < 0.6 and abs(px - last_click[1]) < 40 and abs(py - last_click[2]) < 40)
                    if not same:
                        self.stage("2단계 · 당기기")
                        self.click_at(mon, px, py)
                        self.stats["pulls"] += 1
                        last_click = (time.time(), px, py)
                        t_pull = time.time()
                        phase = "pull"
                        self.log("당기기 클릭 (일치도 %.2f)" % sc)
                        time.sleep(0.12)
                    continue

                if phase == "cooldown":
                    self.stage("쿨다운")
                    if now >= t_next:
                        phase = "cast"
                elif phase == "cast":
                    self.cast(mon)
                    phase, t_cast = "wait", time.time()
                elif phase == "wait":
                    self.stage("입질 대기")
                    if now - t_cast > float(self.cfg["bite_timeout"]):
                        self.log("입질 없음 → 재캐스팅")
                        phase = "cast"
                elif phase == "pull":
                    self.stage("당기기 대기")
                    if now - t_pull > 15:
                        self.log("진행 멈춤 → 재캐스팅")
                        phase = "cast"
                time.sleep(0.01)

    # ---------- 인식 테스트 ----------
    def snapshot(self):
        """현재 화면에서 무엇이 인식되는지 확인하고 표시된 스크린샷을 바탕화면에 저장."""
        with mss.mss() as sct:
            mon = self.monitor(sct)
            frame, _, _ = self.grab(sct, mon)
            frame = frame.copy()
            t0 = time.perf_counter()
            g = is_final(frame)
            pull = find_pull(frame, self.tpl, float(self.cfg["pull_sens"]))
            ms_ = (time.perf_counter() - t0) * 1000
        img = np.ascontiguousarray(frame[:, :, :3])
        msg = []
        if pull:
            x, y, sc = pull
            cv2.circle(img, (int(x), int(y)), 40, (0, 255, 0), 3)
            cv2.putText(img, "PULL %.2f" % sc, (int(x) - 40, int(y) - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            msg.append("당기기 버튼 인식됨 (%.2f)" % sc)
        else:
            msg.append("당기기 버튼 없음")
        if g:
            cx = find_capsule(frame, g)
            cv2.rectangle(img, (int(g["x"]) - 20, g["top"] - 6), (int(g["x"]) + 20, g["bottom"] + 6), (0, 255, 255), 2)
            if cx is not None:
                cv2.line(img, (int(cx), g["bottom"]), (int(cx), g["bottom"] + 60), (255, 0, 255), 2)
            msg.append("게이지 인식됨")
        else:
            msg.append("게이지 없음")
        msg.append("처리 %.0fms" % ms_)
        ok, buf = cv2.imencode(".png", img)
        path = ""
        if ok:
            desk = os.path.join(os.path.expanduser("~"), "Desktop")
            folder = desk if os.path.isdir(desk) else data_dir()
            path = os.path.join(folder, "AutoFish_인식테스트.png")
            try:
                with open(path, "wb") as f:
                    f.write(buf.tobytes())
            except Exception:
                path = ""
        return " / ".join(msg), path


# =====================================================================
#  UI (순수 tkinter, 다크 테마)
# =====================================================================
BG, CARD, LINE = "#0d1015", "#161a21", "#262c37"
TEXT, MUTED = "#e8ebf1", "#8b94a7"
ACC, OK, BAD, WARN = "#5b8cff", "#34d399", "#f87171", "#fbbf24"
FONT = "Malgun Gothic" if sys.platform == "win32" else ("NanumGothic" if sys.platform.startswith("linux") else "Apple SD Gothic Neo")


def rrect(c, x1, y1, x2, y2, r, **kw):
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2, x2 - r, y2,
           x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return c.create_polygon(pts, smooth=True, **kw)


def build_ui_classes(tk, ui):
    S = lambda v: int(round(v * ui))

    class Btn(tk.Canvas):
        def __init__(self, master, text, command, bg=ACC, fg="#ffffff", hover=None, h=44, size=11, bold=True):
            super().__init__(master, height=S(h), bg=master["bg"], highlightthickness=0, bd=0, cursor="hand2")
            self.text, self.command, self.c_bg, self.fg = text, command, bg, fg
            self.c_hover = hover or bg
            self.size, self.bold, self.cur = size, bold, bg
            self.bind("<Configure>", lambda e: self.draw())
            self.bind("<Enter>", lambda e: self._set_cur(self.c_hover))
            self.bind("<Leave>", lambda e: self._set_cur(self.c_bg))
            self.bind("<ButtonRelease-1>", lambda e: self.command())

        def _set_cur(self, c):
            self.cur = c
            self.draw()

        def draw(self):
            self.delete("all")
            w, h = self.winfo_width(), self.winfo_height()
            rrect(self, 1, 1, w - 1, h - 1, S(12), fill=self.cur, outline="")
            self.create_text(w / 2, h / 2, text=self.text, fill=self.fg,
                             font=(FONT, self.size, "bold" if self.bold else "normal"))

        def set(self, text=None, bg=None, hover=None, fg=None):
            if text is not None:
                self.text = text
            if bg is not None:
                self.c_bg, self.cur = bg, bg
            if hover is not None:
                self.c_hover = hover
            if fg is not None:
                self.fg = fg
            self.draw()

    class Pill(tk.Canvas):
        def __init__(self, master):
            super().__init__(master, width=S(130), height=S(30), bg=master["bg"], highlightthickness=0, bd=0)
            self.text, self.color = "정지됨", MUTED
            self.draw()

        def draw(self):
            self.delete("all")
            w, h = int(self["width"]), int(self["height"])
            rrect(self, 1, 1, w - 1, h - 1, S(14), fill=CARD, outline=LINE)
            self.create_oval(S(12), h / 2 - S(4), S(20), h / 2 + S(4), fill=self.color, outline="")
            self.create_text(S(28), h / 2, text=self.text, fill=TEXT, anchor="w", font=(FONT, 9, "bold"))

        def set(self, text, color):
            self.text, self.color = text, color
            self.draw()

    class StatCard(tk.Canvas):
        def __init__(self, master, caption):
            super().__init__(master, height=S(70), bg=master["bg"], highlightthickness=0, bd=0)
            self.caption, self.value = caption, "0"
            self.bind("<Configure>", lambda e: self.draw())

        def draw(self):
            self.delete("all")
            w, h = self.winfo_width(), self.winfo_height()
            rrect(self, 1, 1, w - 1, h - 1, S(12), fill=CARD, outline=LINE)
            self.create_text(w / 2, h * 0.40, text=self.value, fill=TEXT, font=(FONT, 17, "bold"))
            self.create_text(w / 2, h * 0.76, text=self.caption, fill=MUTED, font=(FONT, 8))

        def set(self, v):
            v = str(v)
            if v != self.value:
                self.value = v
                self.draw()

    class Slider(tk.Canvas):
        def __init__(self, master, label, lo, hi, step, value, fmt, on_change):
            super().__init__(master, height=S(46), bg=master["bg"], highlightthickness=0, bd=0, cursor="hand2")
            self.label, self.lo, self.hi, self.step = label, lo, hi, step
            self.val, self.fmt, self.on_change = value, fmt, on_change
            self.bind("<Configure>", lambda e: self.draw())
            self.bind("<Button-1>", self.drag)
            self.bind("<B1-Motion>", self.drag)

        def draw(self):
            self.delete("all")
            w = self.winfo_width()
            r, y, pad = S(8), S(34), S(10)
            x0, x1 = pad, max(pad + 10, w - pad)
            self.create_text(0, S(10), text=self.label, anchor="w", fill=MUTED, font=(FONT, 9))
            self.create_text(w, S(10), text=self.fmt(self.val), anchor="e", fill=TEXT, font=(FONT, 9, "bold"))
            frac = (self.val - self.lo) / float(self.hi - self.lo)
            xk = x0 + (x1 - x0) * frac
            self.create_line(x0, y, x1, y, width=S(4), fill=LINE, capstyle="round")
            self.create_line(x0, y, xk, y, width=S(4), fill=ACC, capstyle="round")
            self.create_oval(xk - r, y - r, xk + r, y + r, fill="#ffffff", outline=ACC, width=S(2))

        def drag(self, e):
            w = self.winfo_width()
            pad = S(10)
            frac = min(1.0, max(0.0, (e.x - pad) / float(max(1, w - 2 * pad))))
            v = self.lo + frac * (self.hi - self.lo)
            v = round(v / self.step) * self.step
            v = min(self.hi, max(self.lo, v))
            if abs(v - self.val) > 1e-9:
                self.val = v
                self.draw()
                self.on_change(v)

        def set(self, v):
            self.val = v
            self.draw()

    class Switch(tk.Canvas):
        def __init__(self, master, value, on_change):
            super().__init__(master, width=S(44), height=S(24), bg=master["bg"], highlightthickness=0, bd=0, cursor="hand2")
            self.value, self.on_change = value, on_change
            self.bind("<Button-1>", self.toggle)
            self.draw()

        def draw(self):
            self.delete("all")
            w, h = S(44), S(24)
            rrect(self, 1, 1, w - 1, h - 1, S(11), fill=ACC if self.value else LINE, outline="")
            x = w - S(13) if self.value else S(13)
            self.create_oval(x - S(8), h / 2 - S(8), x + S(8), h / 2 + S(8), fill="#ffffff", outline="")

        def toggle(self, e=None):
            self.value = not self.value
            self.draw()
            self.on_change(self.value)

    return S, Btn, Pill, StatCard, Slider, Switch


class App:
    def __init__(self):
        import tkinter as tk
        self.tk = tk
        self.root = tk.Tk()
        r = self.root
        r.title("AutoFish")
        r.configure(bg=BG)
        self.ui = max(1.0, min(3.0, r.winfo_fpixels("1i") / 96.0))
        self.S, Btn, Pill, StatCard, Slider, Switch = build_ui_classes(tk, self.ui)
        S = self.S
        self.cfg = load_settings()
        self.q = queue.Queue()
        self.bot = Bot(self.cfg, self.q)
        self.bot.start()
        self.counting, self.count = False, 0
        self._save_job = None

        r.geometry("%dx%d" % (S(440), min(S(790), r.winfo_screenheight() - S(100))))
        r.minsize(S(420), S(520))
        r.attributes("-topmost", bool(self.cfg["topmost"]))
        pad = S(18)

        # --- 헤더 ---
        hdr = tk.Frame(r, bg=BG)
        hdr.pack(fill="x", padx=pad, pady=(pad, S(2)))
        tk.Label(hdr, text="AutoFish", font=(FONT, 20, "bold"), fg=TEXT, bg=BG).pack(side="left")
        self.pill = Pill(hdr)
        self.pill.pack(side="right")
        tk.Label(r, text="로블록스 자동 낚시  ·  F6 시작/정지  ·  F7 종료", font=(FONT, 9), fg=MUTED, bg=BG,
                 anchor="w").pack(fill="x", padx=pad)

        # --- 메인 버튼 ---
        self.main_btn = Btn(r, "시작", self.toggle, bg=OK, hover="#2bbf8a", fg="#04130c", h=54, size=13)
        self.main_btn.pack(fill="x", padx=pad, pady=(S(14), S(10)))

        # --- 통계 ---
        row = tk.Frame(r, bg=BG)
        row.pack(fill="x", padx=pad)
        for i in range(3):
            row.columnconfigure(i, weight=1, uniform="s")
        self.card_catch, self.card_pull, self.card_time = StatCard(row, "낚은 횟수"), StatCard(row, "당기기 클릭"), StatCard(row, "가동 시간")
        for i, c in enumerate((self.card_catch, self.card_pull, self.card_time)):
            c.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else S(4), 0 if i == 2 else S(4)))
        self.card_time.value = "00:00"

        # --- 상태 ---
        st = tk.Frame(r, bg=CARD, highlightbackground=LINE, highlightthickness=1)
        st.pack(fill="x", padx=pad, pady=(S(12), 0))
        top = tk.Frame(st, bg=CARD)
        top.pack(fill="x", padx=S(14), pady=(S(10), S(4)))
        tk.Label(top, text="현재 단계", font=(FONT, 9), fg=MUTED, bg=CARD).pack(side="left")
        self.stage_lbl = tk.Label(top, text="대기", font=(FONT, 10, "bold"), fg=TEXT, bg=CARD)
        self.stage_lbl.pack(side="right")
        dots = tk.Frame(st, bg=CARD)
        dots.pack(fill="x", padx=S(14), pady=(0, S(10)))
        self.dot_pull = self._dot(dots, "당기기 버튼")
        self.dot_final = self._dot(dots, "게이지")

        # --- 설정 ---
        sc = tk.Frame(r, bg=CARD, highlightbackground=LINE, highlightthickness=1)
        sc.pack(fill="x", padx=pad, pady=(S(12), 0))
        inner = tk.Frame(sc, bg=CARD)
        inner.pack(fill="x", padx=S(14), pady=S(10))
        tk.Label(inner, text="설정", font=(FONT, 10, "bold"), fg=TEXT, bg=CARD, anchor="w").pack(fill="x", pady=(0, S(2)))
        self.sliders = {}
        specs = [
            ("charge_time", "차징 시간", 0.2, 4.0, 0.05, lambda v: "%.2f초" % v),
            ("pull_sens", "당기기 인식 기준 (낮을수록 관대)", 0.30, 0.90, 0.01, lambda v: "%.2f" % v),
            ("bite_timeout", "입질 없을 때 재캐스팅", 10.0, 120.0, 1.0, lambda v: "%d초" % v),
            ("after_delay", "낚은 뒤 다음 캐스팅까지", 0.5, 8.0, 0.1, lambda v: "%.1f초" % v),
            ("lead", "게이지 예측 보정", 0.0, 0.30, 0.01, lambda v: "%.2f초" % v),
        ]
        for key, label, lo, hi, step, fmt in specs:
            s = Slider(inner, label, lo, hi, step, float(self.cfg[key]), fmt, lambda v, k=key: self.on_setting(k, v))
            s.pack(fill="x")
            self.sliders[key] = s
        sw = tk.Frame(inner, bg=CARD)
        sw.pack(fill="x", pady=(S(4), 0))
        tk.Label(sw, text="항상 위에 표시", font=(FONT, 9), fg=MUTED, bg=CARD).pack(side="left")
        self.sw_top = Switch(sw, bool(self.cfg["topmost"]), self.on_topmost)
        self.sw_top.pack(side="right")

        # --- 모니터 선택 (2개 이상일 때만) ---
        try:
            with mss.mss() as sct:
                nmon = len(sct.monitors) - 1
        except Exception:
            nmon = 1
        self.mon_btns = []
        if nmon > 1:
            mf = tk.Frame(inner, bg=CARD)
            mf.pack(fill="x", pady=(S(8), 0))
            tk.Label(mf, text="캡처 모니터", font=(FONT, 9), fg=MUTED, bg=CARD).pack(side="left")
            for i in range(1, nmon + 1):
                b = Btn(mf, str(i), lambda i=i: self.set_monitor(i), bg=LINE, hover="#323a48", h=28, size=9)
                b.configure(width=S(34))
                b.pack(side="right", padx=(S(4), 0))
                self.mon_btns.append(b)
            self.set_monitor(int(self.cfg["monitor"]) if int(self.cfg["monitor"]) <= nmon else 1, save=False)

        # --- 보조 버튼 ---
        br = tk.Frame(r, bg=BG)
        br.pack(fill="x", padx=pad, pady=(S(12), 0))
        br.columnconfigure(0, weight=1, uniform="b")
        br.columnconfigure(1, weight=1, uniform="b")
        Btn(br, "인식 테스트", self.test_detect, bg=CARD, hover="#1f2430", fg=TEXT, h=40, size=10).grid(row=0, column=0, sticky="ew", padx=(0, S(4)))
        Btn(br, "기본값으로", self.reset_defaults, bg=CARD, hover="#1f2430", fg=TEXT, h=40, size=10).grid(row=0, column=1, sticky="ew", padx=(S(4), 0))

        # --- 로그 ---
        lf = tk.Frame(r, bg=CARD, highlightbackground=LINE, highlightthickness=1)
        lf.pack(fill="both", expand=True, padx=pad, pady=(S(12), pad))
        self.logbox = tk.Text(lf, height=6, bg=CARD, fg=MUTED, bd=0, highlightthickness=0, wrap="word",
                              font=(FONT, 9), state="disabled", padx=S(10), pady=S(8), insertbackground=CARD)
        self.logbox.pack(fill="both", expand=True)

        r.protocol("WM_DELETE_WINDOW", self.close)
        self.listener = keyboard.Listener(on_press=self.on_key, daemon=True)
        self.listener.start()
        self.log("준비 완료. 시작을 누르면 3초 뒤 작동합니다. 그 사이 로블록스 화면을 클릭하세요.")
        self.poll()

    # ---------- 작은 UI 조각 ----------
    def _dot(self, parent, text):
        tk = self.tk
        f = tk.Frame(parent, bg=CARD)
        f.pack(side="left", padx=(0, self.S(18)))
        c = tk.Canvas(f, width=self.S(10), height=self.S(10), bg=CARD, highlightthickness=0, bd=0)
        c.pack(side="left", padx=(0, self.S(6)))
        c.create_oval(1, 1, self.S(10) - 1, self.S(10) - 1, fill=LINE, outline="", tags="d")
        tk.Label(f, text=text, font=(FONT, 9), fg=MUTED, bg=CARD).pack(side="left")
        return c

    def _dot_set(self, c, on):
        c.itemconfigure("d", fill=OK if on else LINE)

    def log(self, msg):
        b = self.logbox
        b.configure(state="normal")
        b.insert("end", time.strftime("%H:%M:%S  ") + msg + "\n")
        n = int(b.index("end-1c").split(".")[0])
        if n > 300:
            b.delete("1.0", "%d.0" % (n - 300))
        b.see("end")
        b.configure(state="disabled")

    # ---------- 동작 ----------
    def on_key(self, key):  # 다른 스레드에서 호출되므로 큐로만 전달
        if key == keyboard.Key.f6:
            self.q.put(("hotkey", "f6"))
        elif key == keyboard.Key.f7:
            self.q.put(("hotkey", "f7"))

    def toggle(self, countdown=3):
        if self.counting:
            self.counting = False
            self._set_stopped()
            self.log("시작 취소")
            return
        if self.bot.running:
            self.stop_bot()
            return
        if countdown <= 0:
            self.start_bot()
            return
        self.counting, self.count = True, countdown
        self.main_btn.set("취소", bg=WARN, hover="#e0a91c", fg="#201700")
        self._tick()

    def _tick(self):
        if not self.counting:
            return
        if self.count <= 0:
            self.counting = False
            self.start_bot()
            return
        self.pill.set("%d초 뒤 시작" % self.count, WARN)
        self.count -= 1
        self.root.after(1000, self._tick)

    def start_bot(self):
        self.bot.stats.update(catches=0, pulls=0, casts=0, t0=time.time())
        self.bot.running = True
        self.pill.set("작동 중", OK)
        self.main_btn.set("정지", bg=BAD, hover="#e05a5a", fg="#1c0707")
        self.log("시작")

    def stop_bot(self):
        self.bot.running = False
        self.bot.release_all()
        self._set_stopped()
        self.log("정지")

    def _set_stopped(self):
        self.pill.set("정지됨", MUTED)
        self.main_btn.set("시작", bg=OK, hover="#2bbf8a", fg="#04130c")

    def on_setting(self, key, v):
        self.cfg[key] = float(v)
        self._save_later()

    def on_topmost(self, v):
        self.cfg["topmost"] = bool(v)
        self.root.attributes("-topmost", bool(v))
        self._save_later()

    def set_monitor(self, i, save=True):
        self.cfg["monitor"] = int(i)
        for k, b in enumerate(self.mon_btns, start=1):
            b.set(bg=ACC if k == i else LINE, hover=ACC if k == i else "#323a48")
        if save:
            self._save_later()

    def reset_defaults(self):
        for k, v in DEFAULTS.items():
            self.cfg[k] = v
        for k, s in self.sliders.items():
            s.set(float(DEFAULTS[k]))
        self.sw_top.value = bool(DEFAULTS["topmost"])
        self.sw_top.draw()
        self.root.attributes("-topmost", bool(DEFAULTS["topmost"]))
        if self.mon_btns:
            self.set_monitor(1, save=False)
        self._save_later()
        self.log("설정을 기본값으로 되돌렸습니다")

    def test_detect(self):
        try:
            msg, path = self.bot.snapshot()
            self.log("인식 테스트: " + msg)
            if path:
                self.log("스크린샷 저장: " + path)
        except Exception as e:
            self.log("인식 테스트 실패: %s" % e)

    def _save_later(self):
        if self._save_job:
            self.root.after_cancel(self._save_job)
        self._save_job = self.root.after(500, lambda: save_settings(self.cfg))

    # ---------- 주기 처리 ----------
    def poll(self):
        try:
            while True:
                ev = self.q.get_nowait()
                if ev[0] == "log":
                    self.log(ev[1])
                elif ev[0] == "stage":
                    self.stage_lbl.config(text=ev[1])
                elif ev[0] == "detect":
                    self._dot_set(self.dot_pull, ev[1])
                    self._dot_set(self.dot_final, ev[2])
                elif ev[0] == "hotkey":
                    if ev[1] == "f6":
                        self.toggle(countdown=0)
                    else:
                        self.close()
                        return
        except queue.Empty:
            pass
        r = self.root
        self.bot.gui_rect = (r.winfo_rootx(), r.winfo_rooty(), r.winfo_rootx() + r.winfo_width(), r.winfo_rooty() + r.winfo_height())
        s = self.bot.stats
        self.card_catch.set(s["catches"])
        self.card_pull.set(s["pulls"])
        if s["t0"] and self.bot.running:
            sec = int(time.time() - s["t0"])
            self.card_time.set("%02d:%02d" % (sec // 60, sec % 60) if sec < 3600 else "%d:%02d:%02d" % (sec // 3600, sec // 60 % 60, sec % 60))
        r.after(80, self.poll)

    def close(self):
        self.bot.running = False
        self.bot.quit = True
        self.bot.release_all()
        save_settings(self.cfg)
        try:
            self.listener.stop()
        except Exception:
            pass
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def main():
    try:
        App().run()
    except Exception:
        err = traceback.format_exc()
        try:
            with open(os.path.join(data_dir(), "crash.log"), "a", encoding="utf-8") as f:
                f.write(err + "\n")
            import tkinter
            from tkinter import messagebox
            tkinter.Tk().withdraw()
            messagebox.showerror("AutoFish 오류", err[-800:] + "\n\n(%s 에 저장됨)" % os.path.join(data_dir(), "crash.log"))
        except Exception:
            pass


if __name__ == "__main__":
    main()
