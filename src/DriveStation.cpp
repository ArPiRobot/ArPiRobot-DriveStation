
#include <DriveStation.h>

#include <QFile>
#include <QPalette>

DriveStation::DriveStation(QWidget *parent){
    
    ui.setupUi(this);

    // Append version to window title
    QFile versionFile(":/version.txt");
    if(versionFile.open(QIODevice::ReadOnly)){
        QString ver = versionFile.readLine().replace("\n", "").replace("\r", "");
        setWindowTitle(windowTitle() + " v" + ver);
    }
}
