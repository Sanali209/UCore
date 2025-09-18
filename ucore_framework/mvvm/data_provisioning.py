from typing import Any, List, Callable, Optional
from loguru import logger

class DataProvisioningMixin:
    """
    Mixin for flexible data provisioning and on-demand loading.
    Supports 'provide all', 'provide visible', batch, and async modes.
    """
    def __init__(self):
        self.provision_mode: str = "all"  # "all" or "visible"
        self.batch_size: Optional[int] = None
        self.async_loader: Optional[Callable[..., Any]] = None

    def set_provision_mode(self, mode: str):
        logger.info(f"DataProvisioningMixin: set_provision_mode {mode}")
        assert mode in ("all", "visible")
        self.provision_mode = mode

    def set_batch_size(self, size: int):
        logger.info(f"DataProvisioningMixin: set_batch_size {size}")
        self.batch_size = size

    def set_async_loader(self, loader: Callable[..., Any]):
        logger.info("DataProvisioningMixin: set_async_loader")
        self.async_loader = loader

    def provide_data(self, data: List[Any], visible_indices: Optional[List[int]] = None) -> List[Any]:
        if self.provision_mode == "all" or visible_indices is None:
            logger.info("DataProvisioningMixin: provide all data")
            return data
        logger.info("DataProvisioningMixin: provide visible data only")
        return [data[i] for i in visible_indices if 0 <= i < len(data)]

    async def provide_data_async(self, *args, **kwargs):
        if self.async_loader:
            logger.info("DataProvisioningMixin: provide_data_async using async_loader")
            return await self.async_loader(*args, **kwargs)
        raise NotImplementedError("No async_loader set for DataProvisioningMixin.")

    def provide_data_in_batches(self, data: List[Any]) -> List[List[Any]]:
        if not self.batch_size or self.batch_size <= 0:
            logger.info("DataProvisioningMixin: provide all data in one batch")
            return [data]
        logger.info(f"DataProvisioningMixin: provide data in batches of {self.batch_size}")
        return [data[i:i+self.batch_size] for i in range(0, len(data), self.batch_size)]
