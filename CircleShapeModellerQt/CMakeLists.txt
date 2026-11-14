cmake_minimum_required(VERSION 3.21)
project(CircleShapeModeller VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTORCC ON)

find_package(Qt6 6.2 REQUIRED COMPONENTS Widgets)

add_executable(CircleShapeModeller
    src/main.cpp
    src/application/MainWindow.cpp
    src/application/MainWindow.h
    src/canvas/ModelingCanvas.cpp
    src/canvas/ModelingCanvas.h
    src/geometry/Geometry.h
    src/modeling/ShapeModelingMethod.h
    src/modeling/HermiteEnvelope.cpp
    src/modeling/HermiteEnvelope.h
    src/modeling/DiskBezier.cpp
    src/modeling/DiskBezier.h
    src/modeling/ModelingFactory.cpp
    src/modeling/ModelingFactory.h
)

target_link_libraries(CircleShapeModeller PRIVATE Qt6::Widgets)
target_include_directories(CircleShapeModeller PRIVATE src)
target_compile_features(CircleShapeModeller PRIVATE cxx_std_17)

if(MSVC)
    target_compile_options(CircleShapeModeller PRIVATE /W4 /permissive-)
else()
    target_compile_options(CircleShapeModeller PRIVATE -Wall -Wextra -Wpedantic)
endif()

if(WIN32)
    find_program(QT_DEPLOY_TOOL windeployqt
        HINTS "${Qt6_DIR}/../../../bin"
        REQUIRED
    )
    add_custom_command(TARGET CircleShapeModeller POST_BUILD
        COMMAND "${QT_DEPLOY_TOOL}" --no-translations "$<TARGET_FILE:CircleShapeModeller>"
        COMMENT "Deploying Qt runtime dependencies"
    )
endif()

include(CTest)
if(BUILD_TESTING)
    add_executable(GeometryTests
        src/tests/GeometryTests.cpp
        src/modeling/HermiteEnvelope.cpp
        src/modeling/DiskBezier.cpp
    )
    target_include_directories(GeometryTests PRIVATE src)
    add_test(NAME GeometryTests COMMAND GeometryTests)
endif()
