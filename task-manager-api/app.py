from app_factory import create_app
from config.settings import settings

app = create_app()

if __name__ == '__main__':
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
