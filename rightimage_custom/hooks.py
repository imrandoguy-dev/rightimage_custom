app_name = "rightimage_custom"
app_title = "Right Image Custom"
app_publisher = "Hipersign Technologies"
app_description = "Right Image site customizations on top of hiper_solar"
app_email = "support@hipersignerp.com"
app_license = "mit"

# Installed after these, so this app's settings are applied last and win.
required_apps = ["erpnext", "crm", "hiper_solar"]

# This app only belongs on the Right Image site. Installing it anywhere else
# is refused (see install.before_install). Add a site here, or set
# "rightimage_custom_allowed": 1 in that site's site_config.json, to allow it.
ALLOWED_SITES = ["rightimage.hipersignerp.cloud"]

before_install = "rightimage_custom.install.before_install"
after_install = "rightimage_custom.install.after_install"

# Runs after every `bench migrate` (site update, bench change), after
# hiper_solar has synced its fixtures, and puts Right Image's versions back.
after_migrate = "rightimage_custom.install.after_migrate"
