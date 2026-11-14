#pragma once
#include "canvas/ModelingCanvas.h"
#include <QMainWindow>
#include <QSpinBox>
#include <QDoubleSpinBox>
#include <QComboBox>
#include <QLabel>
#include <QCheckBox>
#include <QVector>
#include <QJsonArray>

class MainWindow : public QMainWindow {
    Q_OBJECT
public:
    explicit MainWindow(QWidget* parent=nullptr);
private slots:
    void addCircle(const QPointF& center,double radius);
    void moveCircle(int id,const QPointF& center);
    void selectCircle(int id);
    void generateShape();
    void updateSelectedCircle();
    void deleteSelected();
    void clearAll();
    void saveProject();
    void loadProject();
    void undo();
    void redo();
private:
    void refresh();
    void pushUndo();
    ModelingCanvas* canvas_{};
    QComboBox* method_{};
    QSpinBox* resolution_{};
    QDoubleSpinBox *x_{},*y_{},*radius_{};
    QLabel* status_{};
    QCheckBox *showCircles_{},*showShape_{},*showCenterline_{};
    std::vector<geom::Circle> circles_;
    geom::Shape shape_;
    int selectedId_{-1},nextId_{1};
    QVector<QJsonArray> undoStack_,redoStack_;
};
