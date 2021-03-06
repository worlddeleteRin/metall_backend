from fastapi import Depends, Request
from .models import BaseUser, BaseUserDB, Token, TokenData, BaseUserCreate, BaseUserVerify, BaseUserRestore, BaseUserRestoreVerify, UserDeliveryAddress
from config import settings
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from .jwt import decode_token, create_access_token

from .password import verify_password, get_password_hash

from .user_exceptions import InvalidAuthenticationCredentials, IncorrectVerificationCode, InactiveUser, UserAlreadyExist, UserNotExist, UserDeliveryAddressNotExist, UserNotAdmin



oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")



# authenticate user
def authenticate_user(users_db, username: str, password: str):
	user = get_user(users_db, username)
	if not user:
		return False
	if not verify_password(password, user.hashed_password):
		return False
	return user

def get_user(users_db, username: str):
	user_dict = users_db.find_one({"username": username})
	#print('user dict is', user_dict)
	if user_dict:
		return BaseUserDB(**user_dict)

async def get_current_user(request: Request, token: str = Depends(oauth2_scheme)):
#	print('run get current user, requets is', request)
	try:
		payload = decode_token(token, settings.JWT_SECRET_KEY, [settings.JWT_ALGORITHM])
		#print('payload is', payload)
		username: str = payload.get("sub")
		if username is None:
			raise InvalidAuthenticationCredentials
		token_data = TokenData(username = username)
	except JWTError:
		raise InvalidAuthenticationCredentials
	user = get_user(request.app.users_db, username = token_data.username)
	if user is None:
		raise InvalidAuthenticationCredentials
	return user


def get_current_active_user(request: Request, current_user: BaseUser = Depends(get_current_user)):
	if not current_user.is_active:
		raise InactiveUser
	return current_user

def get_current_admin_user(request: Request, current_user: BaseUser = Depends(get_current_user)):
	if not current_user.is_superuser:
		raise UserNotAdmin
	return current_user

#def check_user_exist(users_db, username):
#	user = users_db.find_one({"username": username})
#	if not user:
#		return False
#	return user

def get_user_register(request: Request, user_info: BaseUserCreate):
	user_info = user_info.dict()
	user = request.app.users_db.find_one({"username": user_info["username"]})
	# if user exist and verified, we raise exist exception
	if user:
		user = BaseUser(**user)
		if user.is_verified:
			raise UserAlreadyExist
		# if user exist, but not verified - we delete it,
		# to recreate in future
		else:
			#print('found user when register, but it is not verified, so, delete it')
			request.app.users_db.delete_one({"_id": user.id})

	user_info["hashed_password"] = get_password_hash(user_info["password"])
	user_to_register = BaseUserDB(**user_info)
	return user_to_register

def get_user_restore(request: Request, user_info: BaseUserRestore):
	#user_info = user_info.dict()
	user = request.app.users_db.find_one({"username": user_info.username})
	# if user not exist we raise not exist exception
	if not user:
		raise UserNotExist

	user_to_verify = BaseUserDB(**user)
	return user_to_verify

def get_user_verify(request: Request, user_info: BaseUserVerify):
	#user_info = user_info.dict()
	user = request.app.users_db.find_one({"username": user_info.username})
	if not user:
		raise UserNotExist
	user = BaseUserDB(**user)
	if not user_info.otp == user.otp:
		raise IncorrectVerificationCode
	# set user to verified
	user.is_verified = True
	user.is_active = True
	user.otp = None
	request.app.users_db.update_one({"_id": user.id}, {"$set": user.dict(by_alias=True)})

	return BaseUser(**user.dict())
#	if user.is_verified:
#		raise UserAlreadyVerified
def get_user_restore_verify(request: Request, user_info: BaseUserRestoreVerify):
	user = request.app.users_db.find_one({"username": user_info.username})
	if not user:
		raise UserNotExist
	user = BaseUserDB(**user)
	if not user_info.otp == user.otp:
		raise IncorrectVerificationCode
	# set user otp code to None 
	user.otp = None
	request.app.users_db.update_one({"_id": user.id}, {"$set": user.dict(by_alias=True)})
	return BaseUser(**user.dict())

def get_user_delivery_address_by_id(users_addresses_db, delivery_address_id):
	print('delivery address is', delivery_address_id)
	address_dict = users_addresses_db.find_one(
		{ "_id": delivery_address_id }
	)
	print('address dict is', address_dict)
	if not address_dict:
		raise UserDeliveryAddressNotExist
	address = UserDeliveryAddress(**address_dict)
	return address
