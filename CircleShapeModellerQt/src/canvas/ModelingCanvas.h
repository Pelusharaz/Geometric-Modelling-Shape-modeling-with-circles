#pragma once
#include "geometry/Geometry.h"
#include <QGraphicsView>
class ModelingCanvas : public QGraphicsView {
    Q_OBJECT
public:
    explicit ModelingCanvas(QWidget* parent=nullptr);
    void setCircles(const std::vector<geom::Circle>& circles);
    void setShape(const geom::Shape& shape);
    void setAddMode(bool enabled);
    void setSelectedId(int id);
    void fitContent();
signals:
    void circleCreated(const QPointF& center, double radius);
    void circleMoved(int id, const QPointF& center);
    void circleDragStarted();
    void circleSelected(int id);
protected:
    void drawBackground(QPainter* painter, const QRectF& rect) override;
    void mousePressEvent(QMouseEvent* event) override;
    void mouseMoveEvent(QMouseEvent* event) override;
    void mouseReleaseEvent(QMouseEvent* event) override;
    void wheelEvent(QWheelEvent* event) override;
private:
    int hitCircle(const QPointF& p) const;
    void rebuildScene();
    std::vector<geom::Circle> circles_;
    geom::Shape shape_;
    bool addMode_{false}, dragging_{false}, panning_{false}, radiusPreview_{false};
    QPointF pendingCenter_, lastMouse_, dragOffset_;
    int selectedId_{-1};
};
