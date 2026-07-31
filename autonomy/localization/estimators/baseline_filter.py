from __future__ import annotations

import math
from typing import Sequence


class Matrix:
    """Numpy kullanmadan küçük boyutlu matris işlemleri için basit sınıf."""
    def __init__(self, data: list[list[float]]):
        self.data = data
        self.rows = len(data)
        self.cols = len(data[0]) if self.rows > 0 else 0

    @classmethod
    def zeros(cls, rows: int, cols: int) -> Matrix:
        return cls([[0.0 for _ in range(cols)] for _ in range(rows)])

    @classmethod
    def eye(cls, size: int) -> Matrix:
        m = cls.zeros(size, size)
        for i in range(size):
            m.data[i][i] = 1.0
        return m

    def transpose(self) -> Matrix:
        return Matrix([[self.data[r][c] for r in range(self.rows)] for c in range(self.cols)])

    def __add__(self, other: Matrix) -> Matrix:
        return Matrix([
            [self.data[r][c] + other.data[r][c] for c in range(self.cols)]
            for r in range(self.rows)
        ])

    def __sub__(self, other: Matrix) -> Matrix:
        return Matrix([
            [self.data[r][c] - other.data[r][c] for c in range(self.cols)]
            for r in range(self.rows)
        ])

    def __mul__(self, other: Matrix | float) -> Matrix:
        if isinstance(other, (float, int)):
            return Matrix([[self.data[r][c] * float(other) for c in range(self.cols)] for r in range(self.rows)])
        
        result = Matrix.zeros(self.rows, other.cols)
        for i in range(self.rows):
            for j in range(other.cols):
                result.data[i][j] = sum(self.data[i][k] * other.data[k][j] for k in range(self.cols))
        return result


class BaselineEkfFilter:
    """Durum: [x, y, yaw, v]
    Girdiler: [a_x, omega_z]
    Ölçümler: x, y (GNSS), yaw (Dual GNSS), v (Odometre)
    """
    
    def __init__(self) -> None:
        # Başlangıç durumu
        self.x = Matrix([[0.0], [0.0], [0.0], [0.0]])
        # Başlangıç kovaryansı
        self.P = Matrix.eye(4) * 1.0
        
        # Süreç gürültüsü
        self.Q = Matrix([
            [0.1, 0.0, 0.0, 0.0],
            [0.0, 0.1, 0.0, 0.0],
            [0.0, 0.0, 0.01, 0.0],
            [0.0, 0.0, 0.0, 0.1]
        ])

    def predict(self, a_x: float, omega_z: float, dt: float) -> None:
        """Kinematik model ile tahmini günceller."""
        if dt <= 0:
            return
            
        px = self.x.data[0][0]
        py = self.x.data[1][0]
        yaw = self.x.data[2][0]
        v = self.x.data[3][0]
        
        # State update
        new_px = px + v * math.cos(yaw) * dt
        new_py = py + v * math.sin(yaw) * dt
        new_yaw = yaw + omega_z * dt
        # Normalize yaw
        new_yaw = (new_yaw + math.pi) % (2 * math.pi) - math.pi
        new_v = v + a_x * dt
        
        self.x = Matrix([[new_px], [new_py], [new_yaw], [new_v]])
        
        # Jacobian F
        F = Matrix([
            [1.0, 0.0, -v * math.sin(yaw) * dt, math.cos(yaw) * dt],
            [0.0, 1.0,  v * math.cos(yaw) * dt, math.sin(yaw) * dt],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ])
        
        # P = F * P * F^T + Q
        self.P = (F * self.P * F.transpose()) + self.Q

    def _scalar_update(self, H: Matrix, z: float, r: float, is_angle: bool = False) -> None:
        """Skaler ölçüm güncellemesi (R diagonal varsayılarak bağımsız uygulanabilir)."""
        # S = H * P * H^T + R
        S = (H * self.P * H.transpose()).data[0][0] + r
        if S < 1e-6:
            return
            
        # K = P * H^T / S
        K = (self.P * H.transpose()) * (1.0 / S)
        
        hx = (H * self.x).data[0][0]
        y = z - hx
        if is_angle:
            y = (y + math.pi) % (2 * math.pi) - math.pi
            
        # x = x + K * y
        self.x = self.x + (K * y)
        if is_angle:
            self.x.data[2][0] = (self.x.data[2][0] + math.pi) % (2 * math.pi) - math.pi
            
        # P = (I - K * H) * P
        I = Matrix.eye(4)
        self.P = (I - (K * H)) * self.P

    def update_gnss(self, pos_x: float, pos_y: float, r_x: float = 2.0, r_y: float = 2.0) -> None:
        H_x = Matrix([[1.0, 0.0, 0.0, 0.0]])
        self._scalar_update(H_x, pos_x, r_x)
        
        H_y = Matrix([[0.0, 1.0, 0.0, 0.0]])
        self._scalar_update(H_y, pos_y, r_y)

    def update_yaw(self, yaw: float, r_yaw: float = 0.5) -> None:
        H_yaw = Matrix([[0.0, 0.0, 1.0, 0.0]])
        self._scalar_update(H_yaw, yaw, r_yaw, is_angle=True)

    def update_velocity(self, v: float, r_v: float = 0.5) -> None:
        H_v = Matrix([[0.0, 0.0, 0.0, 1.0]])
        self._scalar_update(H_v, v, r_v)

    def get_state(self) -> tuple[float, float, float, float]:
        """(x, y, yaw, v) döndürür."""
        return (
            self.x.data[0][0],
            self.x.data[1][0],
            self.x.data[2][0],
            self.x.data[3][0]
        )
        
    def get_covariance(self) -> tuple[float, float, float, float]:
        """Kovaryans matrisinin köşegenini döndürür."""
        return (
            self.P.data[0][0],
            self.P.data[1][1],
            self.P.data[2][2],
            self.P.data[3][3]
        )
