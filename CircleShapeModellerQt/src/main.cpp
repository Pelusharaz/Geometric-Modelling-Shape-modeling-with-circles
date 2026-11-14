#include "application/MainWindow.h"
#include <QApplication>
int main(int argc,char* argv[]){QApplication app(argc,argv);app.setApplicationName("Circle Shape Modeller");app.setOrganizationName("Geometric Modelling Project");app.setStyle("Fusion");MainWindow window;window.show();return app.exec();}
