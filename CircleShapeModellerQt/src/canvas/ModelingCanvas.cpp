#include "ModelingCanvas.h"
#include <QGraphicsScene>
#include <QGraphicsEllipseItem>
#include <QMouseEvent>
#include <QWheelEvent>
#include <QPainter>
#include <QPainterPath>
#include <QPen>
#include <QBrush>
#include <QFont>
#include <QColor>
#include <QScrollBar>
#include <QCursor>
#include <cmath>
#include <algorithm>
ModelingCanvas::ModelingCanvas(QWidget* parent):QGraphicsView(parent){setScene(new QGraphicsScene(this));setRenderHint(QPainter::Antialiasing,true);setDragMode(QGraphicsView::NoDrag);setViewportUpdateMode(QGraphicsView::FullViewportUpdate);setTransformationAnchor(QGraphicsView::AnchorUnderMouse);setBackgroundBrush(QColor("#0b1220"));scene()->setSceneRect(-1000,-700,2000,1400);setMinimumSize(600,420);}
void ModelingCanvas::setCircles(const std::vector<geom::Circle>& c){circles_=c;rebuildScene();}
void ModelingCanvas::setShape(const geom::Shape& s){shape_=s;rebuildScene();}
void ModelingCanvas::setAddMode(bool v){addMode_=v;setCursor(v?Qt::CrossCursor:Qt::ArrowCursor);}
void ModelingCanvas::setSelectedId(int id){selectedId_=id;rebuildScene();}
void ModelingCanvas::fitContent(){
    const QRectF content=scene()->itemsBoundingRect();
    if(content.isEmpty()){
        const QRectF emptyScene(-1000,-700,2000,1400);
        scene()->setSceneRect(emptyScene);
        fitInView(emptyScene,Qt::KeepAspectRatio);
        return;
    }
    const qreal padding=std::max<qreal>(24.0,std::max(content.width(),content.height())*.05);
    const QRectF bounds=content.adjusted(-padding,-padding,padding,padding);
    scene()->setSceneRect(bounds);
    fitInView(bounds,Qt::KeepAspectRatio);
}
int ModelingCanvas::hitCircle(const QPointF& p) const{for(auto it=circles_.rbegin();it!=circles_.rend();++it)if(std::hypot(p.x()-it->center.x,p.y()-it->center.y)<=it->radius+7.0)return it->id;return -1;}
void ModelingCanvas::drawBackground(QPainter* painter,const QRectF& rect){painter->fillRect(rect,QColor("#0b1220"));const double step=50;QPen grid(QColor("#1c2a3e"));grid.setWidthF(.7);painter->setPen(grid);for(int x=int(std::floor(rect.left()/step));x<=int(std::ceil(rect.right()/step));++x)painter->drawLine(QPointF(x*step,rect.top()),QPointF(x*step,rect.bottom()));for(int y=int(std::floor(rect.top()/step));y<=int(std::ceil(rect.bottom()/step));++y)painter->drawLine(QPointF(rect.left(),y*step),QPointF(rect.right(),y*step));QPen axis(QColor("#40536d"));axis.setWidthF(1.2);painter->setPen(axis);painter->drawLine(QPointF(0,rect.top()),QPointF(0,rect.bottom()));painter->drawLine(QPointF(rect.left(),0),QPointF(rect.right(),0));}
void ModelingCanvas::rebuildScene(){scene()->clear();if(shape_.valid){if(!shape_.upper.empty()&&!shape_.lower.empty()){QPainterPath path;path.moveTo(shape_.upper.front().x,shape_.upper.front().y);for(const auto& p:shape_.upper)path.lineTo(p.x,p.y);for(auto it=shape_.lower.rbegin();it!=shape_.lower.rend();++it)path.lineTo(it->x,it->y);path.closeSubpath();auto* item=scene()->addPath(path,QPen(QColor("#38bdf8"),2.5),QBrush(QColor(34,197,94,55)));item->setZValue(1);}if(!shape_.centerline.empty()){QPainterPath center;center.moveTo(shape_.centerline.front().x,shape_.centerline.front().y);for(const auto& p:shape_.centerline)center.lineTo(p.x,p.y);scene()->addPath(center,QPen(QColor("#fbbf24"),1.5,Qt::DashLine))->setZValue(2);}for(const auto& p:shape_.contactPoints)scene()->addEllipse(p.x-3,p.y-3,6,6,QPen(Qt::NoPen),QBrush(QColor("#fb7185")))->setZValue(4);for(const auto& tv:shape_.tangentVectors)scene()->addLine(tv.first.x,tv.first.y,tv.first.x+tv.second.x*.2,tv.first.y+tv.second.y*.2,QPen(QColor("#f59e0b"),1.5))->setZValue(3);}
for(const auto& c:circles_){const QColor stroke=c.id==selectedId_?QColor("#fbbf24"):QColor("#94a3b8");scene()->addEllipse(c.center.x-c.radius,c.center.y-c.radius,2*c.radius,2*c.radius,QPen(stroke,c.id==selectedId_?2.8:1.8),QBrush(QColor(148,163,184,18)))->setZValue(5);scene()->addEllipse(c.center.x-3.5,c.center.y-3.5,7,7,QPen(Qt::NoPen),QBrush(QColor("#e2e8f0")))->setZValue(6);auto* label=scene()->addText(QString("#%1").arg(c.id),QFont("Sans Serif",9));label->setDefaultTextColor(QColor("#cbd5e1"));label->setPos(c.center.x+7,c.center.y+7);label->setZValue(7);}
if(radiusPreview_){const QPointF p=mapToScene(mapFromGlobal(QCursor::pos()));const double r=std::hypot(p.x()-pendingCenter_.x(),p.y()-pendingCenter_.y());scene()->addEllipse(pendingCenter_.x()-r,pendingCenter_.y()-r,2*r,2*r,QPen(QColor("#22c55e"),1.5,Qt::DashLine),QBrush(Qt::NoBrush))->setZValue(8);}}
void ModelingCanvas::mousePressEvent(QMouseEvent* e){const QPointF p=mapToScene(e->position().toPoint());if(e->button()==Qt::MiddleButton||e->button()==Qt::RightButton){panning_=true;lastMouse_=e->position();setCursor(Qt::ClosedHandCursor);return;}if(e->button()!=Qt::LeftButton){QGraphicsView::mousePressEvent(e);return;}if(addMode_){if(!radiusPreview_){pendingCenter_=p;radiusPreview_=true;}else{const double r=std::hypot(p.x()-pendingCenter_.x(),p.y()-pendingCenter_.y());radiusPreview_=false;if(r>2)emit circleCreated(pendingCenter_,r);}rebuildScene();return;}selectedId_=hitCircle(p);emit circleSelected(selectedId_);dragging_=selectedId_>=0;lastMouse_=p;if(dragging_){auto it=std::find_if(circles_.begin(),circles_.end(),[this](const auto& c){return c.id==selectedId_;});if(it!=circles_.end())dragOffset_=QPointF(it->center.x-p.x(),it->center.y-p.y());emit circleDragStarted();}rebuildScene();}
void ModelingCanvas::mouseMoveEvent(QMouseEvent* e){const QPointF p=mapToScene(e->position().toPoint());if(panning_){const QPointF delta=e->position()-lastMouse_;lastMouse_=e->position();horizontalScrollBar()->setValue(horizontalScrollBar()->value()-int(delta.x()));verticalScrollBar()->setValue(verticalScrollBar()->value()-int(delta.y()));return;}if(dragging_&&selectedId_>=0){emit circleMoved(selectedId_,p+dragOffset_);lastMouse_=p;}if(radiusPreview_)rebuildScene();}
void ModelingCanvas::mouseReleaseEvent(QMouseEvent* e){if(e->button()==Qt::MiddleButton||e->button()==Qt::RightButton){panning_=false;setCursor(addMode_?Qt::CrossCursor:Qt::ArrowCursor);return;}if(e->button()==Qt::LeftButton)dragging_=false;}
void ModelingCanvas::wheelEvent(QWheelEvent* e){const double f=e->angleDelta().y()>0?1.15:1.0/1.15;scale(f,f);}
