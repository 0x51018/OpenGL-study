"""
일인칭 3D 가상 공간 시뮬레이션
----------------------------
이 프로그램은 OpenGL을 사용하여 일인칭 시점의 3D 환경을 구현합니다.
WASD 키로 이동하고 마우스로 시점을 변경할 수 있습니다.
"""

import glfw                  # 창 관리 및 입력 처리 라이브러리
from OpenGL.GL import *      # OpenGL 기본 함수
from OpenGL.GLU import *     # OpenGL 유틸리티 함수
import numpy as np           # 수치 연산 라이브러리
import math                  # 수학 함수

###########################################
# 1. 전역 변수 및 설정
###########################################

# 플레이어/카메라 관련 변수
position = [0.0, 1.7, 0.0]   # 카메라 위치 [x, y, z] (y=1.7은 일반적인 사람 눈높이)
yaw = -90.0                  # 수평 회전각 (도 단위, -90도는 -z축 방향을 바라봄)
pitch = 0.0                  # 수직 회전각 (도 단위, 0도는 수평선)
front = [0.0, 0.0, -1.0]     # 시선 방향 벡터 (정규화된 벡터)
up = [0.0, 1.0, 0.0]         # 상단 방향 벡터 (y축 방향)
right = [1.0, 0.0, 0.0]      # 오른쪽 방향 벡터 (x축 방향)

# 마우스 관련 변수
first_mouse = True           # 첫 마우스 입력 여부 (초기 움직임 보정용)
last_x, last_y = 400, 300    # 마지막 마우스 위치 저장
movement_speed = 0.03        # 이동 속도 계수
mouse_sensitivity = 0.1      # 마우스 감도 계수

# 키보드 상태 저장 딕셔너리 (키:눌림 상태)
keys = {
    glfw.KEY_W: False,       # 앞으로 이동
    glfw.KEY_A: False,       # 왼쪽으로 이동
    glfw.KEY_S: False,       # 뒤로 이동
    glfw.KEY_D: False        # 오른쪽으로 이동
}

###########################################
# 2. 콜백 함수 (이벤트 처리)
###########################################

def window_resize(window, width, height):
    """창 크기가 변경될 때 호출되는 콜백 함수
    
    매개변수:
        window: GLFW 창 객체
        width, height: 새로운 창 크기
    """
    # 뷰포트 설정 (그리기 영역 정의)
    glViewport(0, 0, width, height)
    
    # 투영 행렬 설정 (원근감 설정)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()  # 행렬 초기화
    gluPerspective(45, width / height, 0.1, 100.0)  # 45도 시야각, 종횡비, 가까운/먼 클리핑 평면
    
    # 모델뷰 행렬로 돌아가기
    glMatrixMode(GL_MODELVIEW)

def key_callback(window, key, scancode, action, mods):
    """키보드 입력을 처리하는 콜백 함수
    
    매개변수:
        window: GLFW 창 객체
        key: 입력된 키 코드
        scancode: 플랫폼별 스캔 코드
        action: 키 액션 (PRESS, RELEASE, REPEAT)
        mods: 수정자 키 (Shift, Control 등)
    """
    # WASD 키 상태 업데이트
    if key in keys:
        if action == glfw.PRESS:
            keys[key] = True
        elif action == glfw.RELEASE:
            keys[key] = False
    
    # ESC 키를 누르면 커서 잠금 해제
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_NORMAL)

def mouse_button_callback(window, button, action, mods):
    """마우스 버튼 입력을 처리하는 콜백 함수
    
    매개변수:
        window: GLFW 창 객체
        button: 입력된 마우스 버튼
        action: 버튼 액션 (PRESS, RELEASE)
        mods: 수정자 키 (Shift, Control 등)
    """
    # 왼쪽 클릭 시 커서 잠금 (일인칭 시점 모드)
    if button == glfw.MOUSE_BUTTON_LEFT and action == glfw.PRESS:
        glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)

def cursor_position_callback(window, xpos, ypos):
    """마우스 이동을 처리하는 콜백 함수
    
    매개변수:
        window: GLFW 창 객체
        xpos, ypos: 현재 마우스 위치
    """
    global first_mouse, last_x, last_y, yaw, pitch, front, right, up
    
    # 커서가 잠겨 있을 때만 시점 변경 처리
    if glfw.get_input_mode(window, glfw.CURSOR) != glfw.CURSOR_DISABLED:
        return
    
    # 첫 입력 시 갑작스러운 변화 방지
    if first_mouse:
        last_x, last_y = xpos, ypos
        first_mouse = False
    
    # 마우스 이동량 계산
    dx = xpos - last_x
    dy = last_y - ypos  # 반전 (OpenGL과 화면 좌표계 차이)
    last_x, last_y = xpos, ypos
    
    # 감도 적용
    dx *= mouse_sensitivity
    dy *= mouse_sensitivity
    
    # 시야각 업데이트
    yaw += dx   # 좌우 회전
    pitch += dy  # 상하 회전
    
    # 수직 시야 제한 (-89 ~ 89도) - 뒤집힘 방지
    if pitch > 89.0:
        pitch = 89.0
    if pitch < -89.0:
        pitch = -89.0
    
    # 구면 좌표계 -> 카르테시안 좌표계 변환 (시선 방향 벡터 계산)
    front[0] = math.cos(math.radians(yaw)) * math.cos(math.radians(pitch))
    front[1] = math.sin(math.radians(pitch))
    front[2] = math.sin(math.radians(yaw)) * math.cos(math.radians(pitch))
    
    # 벡터 정규화 (크기를 1로 만듦)
    length = math.sqrt(front[0]**2 + front[1]**2 + front[2]**2)
    front[0] /= length
    front[1] /= length
    front[2] /= length
    
    # 오른쪽 벡터 계산 (front 벡터에서 90도 회전)
    right[0] = math.cos(math.radians(yaw) - math.pi/2)
    right[1] = 0
    right[2] = math.sin(math.radians(yaw) - math.pi/2)

###########################################
# 3. 입력 처리 함수
###########################################

def process_input():
    """키보드 입력에 따른 이동 처리 함수"""
    global position
    
    # 앞뒤 이동 (W, S 키)
    if keys[glfw.KEY_W]:  # 앞으로 이동
        position[0] += front[0] * movement_speed
        position[2] += front[2] * movement_speed
    if keys[glfw.KEY_S]:  # 뒤로 이동
        position[0] -= front[0] * movement_speed
        position[2] -= front[2] * movement_speed
    
    # 좌우 이동 (A, D 키)
    if keys[glfw.KEY_D]:  # 오른쪽으로 이동 (A와 D가 바뀌어 있음에 주의)
        position[0] -= right[0] * movement_speed
        position[2] -= right[2] * movement_speed
    if keys[glfw.KEY_A]:  # 왼쪽으로 이동
        position[0] += right[0] * movement_speed
        position[2] += right[2] * movement_speed

###########################################
# 4. 렌더링 함수
###########################################

def draw_cube(x, y, z, size=1.0):
    """3D 큐브를 그리는 함수
    
    매개변수:
        x, y, z: 큐브의 중심 위치
        size: 큐브의 크기
    """
    half = size / 2  # 큐브 변의 절반
    
    # 큐브의 8개 정점 정의 (6개 면 * 4개 정점)
    vertices = [
        # 앞쪽 면 (z+)
        x-half, y-half, z+half,    x+half, y-half, z+half,    x+half, y+half, z+half,    x-half, y+half, z+half,
        # 뒤쪽 면 (z-)
        x-half, y-half, z-half,   x-half, y+half, z-half,   x+half, y+half, z-half,   x+half, y-half, z-half,
        # 윗쪽 면 (y+)
        x-half, y+half, z-half,    x-half, y+half, z+half,    x+half, y+half, z+half,    x+half, y+half, z-half,
        # 아랫쪽 면 (y-)
        x-half, y-half, z-half,   x+half, y-half, z-half,   x+half, y-half, z+half,   x-half, y-half, z+half,
        # 오른쪽 면 (x+)
        x+half, y-half, z-half,    x+half, y+half, z-half,    x+half, y+half, z+half,    x+half, y-half, z+half,
        # 왼쪽 면 (x-)
        x-half, y-half, z-half,   x-half, y-half, z+half,   x-half, y+half, z+half,   x-half, y+half, z-half
    ]
    
    # 각 면에 적용할 색상 (RGB)
    colors = [
        # 앞쪽 면 (빨강)
        1, 0, 0,   1, 0, 0,   1, 0, 0,   1, 0, 0,
        # 뒤쪽 면 (녹색)
        0, 1, 0,   0, 1, 0,   0, 1, 0,   0, 1, 0,
        # 윗쪽 면 (파랑)
        0, 0, 1,   0, 0, 1,   0, 0, 1,   0, 0, 1,
        # 아랫쪽 면 (노랑)
        1, 1, 0,   1, 1, 0,   1, 1, 0,   1, 1, 0,
        # 오른쪽 면 (자홍)
        1, 0, 1,   1, 0, 1,   1, 0, 1,   1, 0, 1,
        # 왼쪽 면 (청록)
        0, 1, 1,   0, 1, 1,   0, 1, 1,   0, 1, 1
    ]
    
    # GL_QUADS: 4개의 정점으로 면을 그림
    glBegin(GL_QUADS)
    for i in range(0, len(vertices), 3):
        glColor3f(colors[i], colors[i+1], colors[i+2])  # 색상 설정
        glVertex3f(vertices[i], vertices[i+1], vertices[i+2])  # 정점 설정
    glEnd()

def draw_grid(size=20, step=1):
    """바닥 격자와 좌표축을 그리는 함수
    
    매개변수:
        size: 격자의 크기 (중심에서 각 방향으로의 거리)
        step: 격자 간격
    """
    # 격자 그리기
    glBegin(GL_LINES)  # 선 그리기 모드
    glColor3f(0.5, 0.5, 0.5)  # 회색
    
    # x축 방향 선 (평행한 여러 선)
    for i in range(-size, size+1, step):
        glVertex3f(i, 0, -size)  # 시작점
        glVertex3f(i, 0, size)   # 끝점
    
    # z축 방향 선 (평행한 여러 선)
    for i in range(-size, size+1, step):
        glVertex3f(-size, 0, i)  # 시작점
        glVertex3f(size, 0, i)   # 끝점
    
    glEnd()
    
    # 좌표축 그리기 (원점에서 시작하는 3개의 선)
    glBegin(GL_LINES)
    # x축 (빨강)
    glColor3f(1, 0, 0)
    glVertex3f(0, 0, 0)       # 원점
    glVertex3f(size, 0, 0)    # x 방향
    
    # y축 (녹색)
    glColor3f(0, 1, 0)
    glVertex3f(0, 0, 0)       # 원점
    glVertex3f(0, size, 0)    # y 방향
    
    # z축 (파랑)
    glColor3f(0, 0, 1)
    glVertex3f(0, 0, 0)       # 원점
    glVertex3f(0, 0, size)    # z 방향
    glEnd()

def draw_world():
    """3D 환경의 모든 객체를 그리는 함수"""
    # 바닥 격자 그리기
    draw_grid()
    
    # 여러 위치에 큐브 배치
    draw_cube(3, 1, -5)        # 위치 (3, 1, -5)에 크기 1인 큐브
    draw_cube(-4, 1, -6)       # 위치 (-4, 1, -6)에 크기 1인 큐브
    draw_cube(0, 1, -10)       # 위치 (0, 1, -10)에 크기 1인 큐브
    draw_cube(5, 1, -3)        # 위치 (5, 1, -3)에 크기 1인 큐브
    draw_cube(-2, 1, -3, 2.0)  # 위치 (-2, 1, -3)에 크기 2인 큐브
    draw_cube(0, 0.5, -20, 4.0)  # 위치 (0, 0.5, -20)에 크기 4인 큐브

###########################################
# 5. 메인 함수 및 프로그램 진입점
###########################################

def main():
    """메인 함수: 프로그램의 초기화 및 메인 루프를 담당"""
    # GLFW 초기화
    if not glfw.init():
        print("GLFW 초기화 실패")
        return

    # 창 생성
    window = glfw.create_window(800, 600, "일인칭 3D 가상 공간", None, None)
    if not window:
        print("창 생성 실패")
        glfw.terminate()
        return

    # OpenGL 컨텍스트 설정
    glfw.make_context_current(window)
    
    # 콜백 함수 등록
    glfw.set_window_size_callback(window, window_resize)  # 창 크기 변경 시
    glfw.set_key_callback(window, key_callback)           # 키보드 입력 시
    glfw.set_mouse_button_callback(window, mouse_button_callback)  # 마우스 버튼 입력 시
    glfw.set_cursor_pos_callback(window, cursor_position_callback)  # 마우스 이동 시
    
    # 초기 설정 - 마우스를 창 중앙에 위치 및 커서 숨김 (일인칭 모드)
    width, height = glfw.get_window_size(window)
    glfw.set_cursor_pos(window, width/2, height/2)
    glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)
    
    # OpenGL 렌더링 설정
    glEnable(GL_DEPTH_TEST)  # 깊이 테스트 활성화 (3D 물체가 올바르게 보이도록)
    glClearColor(0.1, 0.1, 0.1, 1.0)  # 배경색 설정 (짙은 회색)
    
    # 창 크기로 뷰포트 초기 설정
    window_resize(window, width, height)

    # 메인 렌더링 루프
    while not glfw.window_should_close(window):  # 창이 닫힐 때까지 반복
        # 키보드 입력 처리
        process_input()
        
        # 화면 지우기 (색상 및 깊이 버퍼)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # 카메라 설정 (일인칭 시점)
        glLoadIdentity()  # 모델뷰 행렬 초기화
        gluLookAt(
            position[0], position[1], position[2],                        # 카메라 위치
            position[0] + front[0], position[1] + front[1], position[2] + front[2],  # 바라보는 지점
            up[0], up[1], up[2]                                          # 상단 방향
        )
        
        # 3D 환경 그리기
        draw_world()
        
        # 더블 버퍼링 (화면 깜빡임 방지)
        glfw.swap_buffers(window)
        
        # 이벤트 처리
        glfw.poll_events()

    # 종료 처리
    glfw.terminate()

# 프로그램 시작점
if __name__ == "__main__":
    main()