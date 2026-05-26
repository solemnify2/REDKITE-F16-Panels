#include "usb_names.h"

#define PRODUCT_NAME    {'R','E','D','K','I','T','E',' ','F','1','6',' ','L','e','f','t',' ','C','o','n','s','o','l','e'}
#define PRODUCT_NAME_LEN  24

struct usb_string_descriptor_struct usb_string_product_name = {
  2 + PRODUCT_NAME_LEN * 2,
  3,
  PRODUCT_NAME
};
