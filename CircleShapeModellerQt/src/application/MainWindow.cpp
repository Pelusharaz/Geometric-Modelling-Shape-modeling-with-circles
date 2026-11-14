#include "MainWindow.h"
#include "modeling/ModelingFactory.h"
#include <QWidget>
#include <QHBoxLayout>
#include <QVBoxLayout>
#include <QFormLayout>
#include <QPushButton>
#include <QGroupBox>
#include <QFileDialog>
#include <QMessageBox>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QFile>
#include <QMenuBar>
#include <QStatusBar>
#include <QSplitter>
#include <QScrollArea>
#include <QSignalBlocker>
#include <QKeySequence>
#include <algorithm>

MainWindow::MainWindow(QWidget* parent):QMainWindow(parent){
    setWindowTitle("Circle Shape Modeller | Geometric Modelling");resize(1280,820);
    auto* root=new QWidget(this);auto* layout=new QHBoxLayout(root);layout->setContentsMargins(12,12,12,12);layout->setSpacing(12);
    auto* side=new QScrollArea(root);side->setFixedWidth(285);side->setWidgetResizable(true);side->setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOff);side->setVerticalScrollBarPolicy(Qt::ScrollBarAsNeeded);
    auto* sideContent=new QWidget(side);auto* panel=new QVBoxLayout(sideContent);panel->setSpacing(10);
    auto* title=new QLabel("CIRCLE MODELLER");title->setStyleSheet("font-size:18px;font-weight:700;color:#e2e8f0;letter-spacing:1px;");panel->addWidget(title);
    auto* tools=new QGroupBox("TOOLS");auto* toolLayout=new QVBoxLayout(tools);
    auto* add=new QPushButton("＋  Add circle (2 clicks)");auto* select=new QPushButton("Select / move circles");auto* del=new QPushButton("Delete selected");auto* clear=new QPushButton("Clear canvas");
    toolLayout->addWidget(add);toolLayout->addWidget(select);toolLayout->addWidget(del);toolLayout->addWidget(clear);panel->addWidget(tools);
    auto* params=new QGroupBox("SELECTED CIRCLE");auto* form=new QFormLayout(params);
    x_=new QDoubleSpinBox();y_=new QDoubleSpinBox();radius_=new QDoubleSpinBox();
    for(auto* s:{x_,y_}){s->setRange(-10000,10000);s->setDecimals(2);s->setSingleStep(1);}
    radius_->setRange(2,10000);radius_->setDecimals(2);radius_->setSingleStep(1);
    form->addRow("Centre X",x_);form->addRow("Centre Y",y_);form->addRow("Radius",radius_);
    auto* apply=new QPushButton("Apply parameters");form->addRow(apply);panel->addWidget(params);
    auto* modelling=new QGroupBox("MODELLING");auto* modelForm=new QFormLayout(modelling);
    method_=new QComboBox();for(const auto& n:modeling::ModelingFactory::names())method_->addItem(QString::fromStdString(n));
    resolution_=new QSpinBox();resolution_->setRange(8,500);resolution_->setValue(80);
    modelForm->addRow("Method",method_);modelForm->addRow("Resolution",resolution_);
    auto* generate=new QPushButton("Generate shape");generate->setStyleSheet("QPushButton{background:#15803d;color:white;font-weight:700;padding:9px;border-radius:5px;}");modelForm->addRow(generate);panel->addWidget(modelling);
    auto* display=new QGroupBox("DISPLAY");auto* displayLayout=new QVBoxLayout(display);
    showCircles_=new QCheckBox("Show control circles");showCircles_->setChecked(true);showShape_=new QCheckBox("Show generated shape");showShape_->setChecked(true);showCenterline_=new QCheckBox("Show centreline");showCenterline_->setChecked(true);
    displayLayout->addWidget(showCircles_);displayLayout->addWidget(showShape_);displayLayout->addWidget(showCenterline_);panel->addWidget(display);
    auto* history=new QHBoxLayout();auto* undoBtn=new QPushButton("Undo");auto* redoBtn=new QPushButton("Redo");history->addWidget(undoBtn);history->addWidget(redoBtn);panel->addLayout(history);
    auto* files=new QHBoxLayout();auto* save=new QPushButton("Save");auto* load=new QPushButton("Open");files->addWidget(save);files->addWidget(load);panel->addLayout(files);
    auto* fit=new QPushButton("Fit circles to window");panel->addWidget(fit);panel->addStretch();status_=new QLabel("Ready. Add circles to begin.");status_->setWordWrap(true);status_->setStyleSheet("color:#94a3b8;");panel->addWidget(status_);
    side->setWidget(sideContent);
    canvas_=new ModelingCanvas(root);layout->addWidget(side);layout->addWidget(canvas_,1);setCentralWidget(root);
    auto* fileMenu=menuBar()->addMenu("File");fileMenu->addAction("Open project",this,&MainWindow::loadProject);fileMenu->addAction("Save project",this,&MainWindow::saveProject);fileMenu->addSeparator();fileMenu->addAction("Exit",this,&QWidget::close);
    auto* editMenu=menuBar()->addMenu("Edit");editMenu->addAction("Undo",this,&MainWindow::undo,QKeySequence::Undo);editMenu->addAction("Redo",this,&MainWindow::redo,QKeySequence::Redo);
    connect(add,&QPushButton::clicked,this,[this]{canvas_->setAddMode(true);status_->setText("Click once to place a centre, move the mouse, then click again to set the radius.");});
    connect(select,&QPushButton::clicked,this,[this]{canvas_->setAddMode(false);status_->setText("Select a circle to edit it, or drag its centre to move it.");});
    connect(canvas_,&ModelingCanvas::circleCreated,this,&MainWindow::addCircle);connect(canvas_,&ModelingCanvas::circleMoved,this,&MainWindow::moveCircle);connect(canvas_,&ModelingCanvas::circleDragStarted,this,&MainWindow::pushUndo);connect(canvas_,&ModelingCanvas::circleSelected,this,&MainWindow::selectCircle);
    connect(generate,&QPushButton::clicked,this,&MainWindow::generateShape);connect(apply,&QPushButton::clicked,this,&MainWindow::updateSelectedCircle);connect(del,&QPushButton::clicked,this,&MainWindow::deleteSelected);connect(clear,&QPushButton::clicked,this,&MainWindow::clearAll);
    connect(save,&QPushButton::clicked,this,&MainWindow::saveProject);connect(load,&QPushButton::clicked,this,&MainWindow::loadProject);connect(undoBtn,&QPushButton::clicked,this,&MainWindow::undo);connect(redoBtn,&QPushButton::clicked,this,&MainWindow::redo);connect(fit,&QPushButton::clicked,canvas_,&ModelingCanvas::fitContent);
    connect(showCircles_,&QCheckBox::toggled,this,[this]{refresh();});connect(showShape_,&QCheckBox::toggled,this,[this]{refresh();});connect(showCenterline_,&QCheckBox::toggled,this,[this]{refresh();});
    refresh();
}
void MainWindow::pushUndo(){QJsonArray a;for(const auto& c:circles_){QJsonObject o;o["id"]=c.id;o["x"]=c.center.x;o["y"]=c.center.y;o["r"]=c.radius;a.append(o);}undoStack_.append(a);if(undoStack_.size()>50)undoStack_.removeFirst();redoStack_.clear();}
void MainWindow::addCircle(const QPointF& p,double r){pushUndo();circles_.push_back({nextId_++,{p.x(),p.y()},r});selectedId_=circles_.back().id;shape_={};canvas_->setAddMode(false);refresh();status_->setText(QString("Circle %1 added. %2 circles total.").arg(selectedId_).arg(circles_.size()));}
void MainWindow::moveCircle(int id,const QPointF& p){auto it=std::find_if(circles_.begin(),circles_.end(),[id](const auto& c){return c.id==id;});if(it==circles_.end())return;it->center={p.x(),p.y()};shape_={};refresh();}
void MainWindow::selectCircle(int id){selectedId_=id;auto it=std::find_if(circles_.begin(),circles_.end(),[id](const auto& c){return c.id==id;});const bool valid=it!=circles_.end();for(auto* s:{x_,y_,radius_})s->setEnabled(valid);if(valid){QSignalBlocker a(x_),b(y_),c(radius_);x_->setValue(it->center.x);y_->setValue(it->center.y);radius_->setValue(it->radius);}canvas_->setSelectedId(id);}
void MainWindow::updateSelectedCircle(){auto it=std::find_if(circles_.begin(),circles_.end(),[this](const auto& c){return c.id==selectedId_;});if(it==circles_.end())return;pushUndo();it->center={x_->value(),y_->value()};it->radius=radius_->value();shape_={};refresh();}
void MainWindow::deleteSelected(){if(selectedId_<0)return;pushUndo();circles_.erase(std::remove_if(circles_.begin(),circles_.end(),[this](const auto& c){return c.id==selectedId_;}),circles_.end());selectedId_=-1;shape_={};refresh();}
void MainWindow::clearAll(){if(circles_.empty())return;pushUndo();circles_.clear();shape_={};selectedId_=-1;refresh();status_->setText("Canvas cleared.");}
void MainWindow::generateShape(){auto algo=modeling::ModelingFactory::create(method_->currentText().toStdString());if(!algo)return;shape_=algo->generate(circles_,resolution_->value());if(!shape_.valid){QMessageBox::warning(this,"Cannot generate shape",QString::fromStdString(shape_.error));status_->setText(QString::fromStdString(shape_.error));}else{QString msg=QString("Generated using %1.").arg(method_->currentText());for(const auto& w:shape_.warnings)msg+="\n• "+QString::fromStdString(w);status_->setText(msg);}refresh();}
void MainWindow::refresh(){auto visible=circles_;if(!showCircles_->isChecked())visible.clear();canvas_->setCircles(visible);auto s=shape_;if(!showShape_->isChecked())s={};if(!showCenterline_->isChecked())s.centerline.clear();canvas_->setShape(s);canvas_->setSelectedId(selectedId_);}
void MainWindow::saveProject(){const QString path=QFileDialog::getSaveFileName(this,"Save project",{},"Circle modeller project (*.json)");if(path.isEmpty())return;QJsonArray a;for(const auto& c:circles_){QJsonObject o;o["id"]=c.id;o["x"]=c.center.x;o["y"]=c.center.y;o["radius"]=c.radius;a.append(o);}QJsonObject root;root["circles"]=a;root["method"]=method_->currentText();root["resolution"]=resolution_->value();QFile f(path);if(!f.open(QIODevice::WriteOnly)){QMessageBox::warning(this,"Save failed",f.errorString());return;}f.write(QJsonDocument(root).toJson(QJsonDocument::Indented));status_->setText("Project saved.");}
void MainWindow::loadProject(){const QString path=QFileDialog::getOpenFileName(this,"Open project",{},"Circle modeller project (*.json)");if(path.isEmpty())return;QFile f(path);if(!f.open(QIODevice::ReadOnly)){QMessageBox::warning(this,"Open failed",f.errorString());return;}QJsonParseError error;const auto doc=QJsonDocument::fromJson(f.readAll(),&error);if(error.error!=QJsonParseError::NoError||!doc.isObject()){QMessageBox::warning(this,"Invalid project","The selected file is not a valid project JSON.");return;}pushUndo();circles_.clear();nextId_=1;for(const auto v:doc.object().value("circles").toArray()){const auto o=v.toObject();const int id=o.value("id").toInt(nextId_);const double r=o.value("radius").toDouble();if(r<=0)continue;circles_.push_back({id,{o.value("x").toDouble(),o.value("y").toDouble()},r});nextId_=std::max(nextId_,id+1);}const int idx=method_->findText(doc.object().value("method").toString());if(idx>=0)method_->setCurrentIndex(idx);resolution_->setValue(doc.object().value("resolution").toInt(80));selectedId_=-1;shape_={};refresh();status_->setText("Project loaded. Generate the shape to rebuild the preview.");}
void MainWindow::undo(){if(undoStack_.isEmpty())return;QJsonArray current;for(const auto& c:circles_){QJsonObject o;o["id"]=c.id;o["x"]=c.center.x;o["y"]=c.center.y;o["r"]=c.radius;current.append(o);}redoStack_.append(current);const auto a=undoStack_.takeLast();circles_.clear();nextId_=1;for(const auto v:a){const auto o=v.toObject();const int id=o.value("id").toInt();circles_.push_back({id,{o.value("x").toDouble(),o.value("y").toDouble()},o.value("r").toDouble()});nextId_=std::max(nextId_,id+1);}shape_={};selectedId_=-1;refresh();}
void MainWindow::redo(){if(redoStack_.isEmpty())return;QJsonArray current;for(const auto& c:circles_){QJsonObject o;o["id"]=c.id;o["x"]=c.center.x;o["y"]=c.center.y;o["r"]=c.radius;current.append(o);}undoStack_.append(current);const auto a=redoStack_.takeLast();circles_.clear();nextId_=1;for(const auto v:a){const auto o=v.toObject();const int id=o.value("id").toInt();circles_.push_back({id,{o.value("x").toDouble(),o.value("y").toDouble()},o.value("r").toDouble()});nextId_=std::max(nextId_,id+1);}shape_={};selectedId_=-1;refresh();}
