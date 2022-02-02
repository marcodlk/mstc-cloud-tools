"""Validates inputs"""

import traceback

from flask import current_app as app


def validate(inputs):
    if len(inputs) == 0:
        return False, "No inputs included"
    try:
        dat_or_txt_exists = False
        for i in inputs:
            app.logger.info("check: " + i)
            if i.endswith(".dat") or i.endswith(".txt"):
                dat_or_txt_exists = True
                break

        app.logger.info("inputs: " + str(inputs))
        if not dat_or_txt_exists:
            return False, "Either a .dat or .txt file must be included"

    except Exception as e:
        app.logger.warning(traceback.format_exc() + str(e))
        return False, traceback.format_exc() + str(e)

    return True, ""