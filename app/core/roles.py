from enum import Enum


class Role(str, Enum):
    customer = "customer"
    restaurant_owner = "restaurant_owner"
    delivery_partner = "delivery_partner"
    admin = "admin"


DEFAULT_ROLE = Role.customer
ALL_ROLES = [role.value for role in Role]
