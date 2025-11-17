## Chạy code:

```bash
python -m venv venv
source ".venv\Scripts\activate"
pip install pygame
```

## BattleShip

Tổng quan:
    - Game turn base
    - 2 màn hình in-game: sắp xếp tàu & giao tranh
    - 1 màn hình chờ
    - 1 màn hình menu
    - 1 màn hình login

Sân đấu: Sân bắn mỗi bên 10x10 (1-10 | A-J)
Các loại tàu: 4x1, 3x1 (x2), 2x1 (x3), 1x1 (x4)
Mỗi turn: 30s, nếu quá thời gian -> skip turn
Bị bắn trúng sẽ hiện x trên khi vực -> ko cho bắn tiếp
