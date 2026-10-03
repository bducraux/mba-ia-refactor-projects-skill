import logging

from src.app import create_app
from src.config.settings import settings

app = create_app(settings)

if __name__ == "__main__":
    logging.getLogger(__name__).info("Servidor iniciado em http://localhost:%s", settings.PORT)
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
