import uuid
from pymongo import ReturnDocument
from enum import Enum

from typing import Optional, List

from pydantic import UUID4, BaseModel, Field, validator
from datetime import datetime, date



class CouponTypeEnum(str, Enum):
	per_item_discount = "per_item_discount"
	per_total_discount = "per_total_discount"
	percentage_discount = "percentage_discount"

class CouponApplyToEnum(str, Enum):
	products = "products"
	categories = "categories"

class CouponApplyTo(BaseModel):
	entity: CouponApplyToEnum
	ids: List[UUID4]

class BaseCoupon(BaseModel):

	""" Base Coupon Model """
	id: UUID4 = Field(default_factory=uuid.uuid4, alias="_id")
	date_created: Optional[datetime] = Field(default_factory=datetime.utcnow)
	# number of times coupon has been used
	num_uses: int = 0
	name: str
	type: CouponTypeEnum # = CouponTypeEnum.per_item_discount
	# discount, that is need to be applied
	amount: int
	# specify the amount value, that order need to have to apply coupon
	min_purchase: int = 0
	# specify the date, when coupon is expires
	expires: Optional[str] = None # must be in datetime format
	enabled: bool = True
	# unique value, that customer will specify to apply coupon
	code: str
	applies_to: CouponApplyTo


