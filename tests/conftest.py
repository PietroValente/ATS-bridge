import os
import sys

# Make push_data_manager modules importable for unit tests.
# The adapters and managers do not depend on Django being configured.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "push_data_manager"))

# Make talent_pool modules importable for unit tests.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "talent_pool"))
