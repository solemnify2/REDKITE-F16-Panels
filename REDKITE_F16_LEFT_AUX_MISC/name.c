#include "usb_names.h"

struct usb_string_descriptor_struct usb_string_product_name = {
  2 + 25 * 2,  // 2 + (글자수 * 2)
  3,
  {'R','E','D','K','I','T','E',' ','F','1','6',' ','L','e','f','t',' ','A','u','x',' ','M','i','s','c'}
};
