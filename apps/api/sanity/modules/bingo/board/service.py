from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import BoardUpdate, TileCreate, TileUpdate


class BoardService:
    async def update_board_by_id(self, *, db: AsyncSession, board_id: int, body: BoardUpdate):
        pass

    async def create_tile_by_board_id(self, *, db: AsyncSession, board_id: int, body: TileCreate):
        pass

    async def get_tile_by_id(self, *, db: AsyncSession, tile_id: int):
        pass

    async def update_tile_by_id(self, *, db: AsyncSession, tile_id: int, body: TileUpdate):
        pass

    async def delete_tile_by_id(self, *, db: AsyncSession, tile_id: int):
        pass


board_service = BoardService()
