
#include <QApplication>

#include <DriveStation.h>

int main(int argc, char **argv){
    QApplication::setAttribute(Qt::AA_EnableHighDpiScaling);
    QApplication::setAttribute(Qt::AA_UseHighDpiPixmaps);
    QApplication app(argc, argv);
    DriveStation ds;
    ds.show();
    app.exec();
}
