import logging
import warnings


def main(capture=True):
    log = logging.getLogger(__name__)
    if capture:
        logging.captureWarnings(True)
    else:
        logging.captureWarnings(False)
    warnings.warn("Look out!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
