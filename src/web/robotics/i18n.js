const en = {
  "page_title": "Personal Projects",
  "page_intro": "Autonomous Systems · Mechatronics · Full-Stack Engineering",
  "contact_label": "Contact:",
  "nav_toggle_show": "▼ Project Overview",
  "nav_toggle_hide": "▲ Project Overview",
  "nav_mk3": "Wyvern MK3 — FPV Quadcopter",
  "nav_long_range": "Wyvern MK2 — Long Range Drone",
  "nav_nori_f411": "Nori F411 (PCB)",
  "nav_micro_fpv": "Micro FPV Drone",
  "nav_uav_controller": "UAV Controller",
  "nav_esp32_lidar": "ESP32 LiDAR Bot",
  "nav_gearbox": "Wolfrom Bilateral Gearbox Actuator",
  "nav_manual_racer": "Wyvern MK1 — Racing Drone",
  "nav_7dof": "7 DOF Robot Arm",
  "nav_diff_drive": "Differential-Drive Mobile Robot",
  "nav_rl_drone": "RL Racing Drone",
  "nav_esp32_fc": "ESP32 Flight Controller (PCB)",
  "mk3_title": "Wyvern MK3 - Autonomous FPV Quadcopter",
  "mk3_p1": "Third-generation Wyvern drone, a 3-inch FPV quadcopter. Hardware design, firmware, RF communication, and embedded flight systems have all been iterated across previous generations, alongside testing of off-the-shelf solutions. MK3 brings together lessons from both approaches.",
  "mk3_p2": "The MK3 exists in two variants: a cruise/FPV quad, and an autonomous flight variant (GPS & GPS-denied using optical flow, range finder, IMU, barometer, compass, etc). Autonomy runs on ArduPilot, PX4, and my custom firmware - altitude/position hold, loiter, GPS waypoints. Supports motors 1104 to 1505, 2S Li-ion to 6S LiPo. CNC carbon fiber frame, TPU printed mounts. Compatible with DJI O4 Lite/Pro.",
  "mk3_video_caption": "Flight maneuvers and high-altitude cruise.",
  "mk3_o4_video_caption": "Flight maneuvers and high-altitude cruise (O4 Lite).",
  "mk3_rescue_video_caption": "Auto rescue and return home (O4 Pro).",
  "mk3_render_caption": "Wyvern MK3 - CAD rendering",
  "mk3_proto1_caption": "Wyvern MK3 - prototype",
  "mk3_build1_caption": "Wyvern MK3 - build",
  "mk3_cad_caption": "Wyvern MK3 - final CAD",
  "mk3_proto2_caption": "Wyvern MK3 - prototype",
  "mk3_build2_caption": "Wyvern MK3 - build",
  "mk3_auto1_caption": "Wyvern MK3 - autonomous variant",
  "longrange_title": "Wyvern MK2 — Long Range Drone",
  "longrange_p1": "Designed and iterated a custom 3.5-inch quadcopter across multiple prototype revisions, including mechanical design, PCB design, embedded systems, fabrication, and structural integration. The carbon fiber frame is fabricated by machining partners, while all mounting hardware and integration components are custom-designed and 3D printed. Full FPV system with onboard camera and live video transmission.",
  "longrange_p2": "Powered by 1–2S 18650 Li-ion packs, the sub-250g quadcopter uses 1202.5 BLDC motors and achieves 20–25 minutes of flight time. Firmware stack primarily uses Betaflight, with additional support and testing across custom firmware, iNav, and ArduPilot configurations. Integrated GPS enables waypoint navigation and GPS rescue/safe-return functionality.",
  "longrange_video_caption": "Holding altitude and rotating to survey the surroundings, then cruising over a river.",
  "norif411_title": "Nori F411 - Custom PCB Flight Controller",
  "norif411_p1": "A custom flight controller PCB designed in Altium Designer, built around the STM32F411 MCU with an onboard MPU6050 IMU providing gyroscope and accelerometer data for flight stabilization. Designed to run a custom port of Betaflight firmware tailored for this board, with the autopilot control stack derived from my <a href=\"#proj-uav-controller\">UAV Controller project</a>.",
  "norif411_p2": "Supports ELRS, TBS Crossfire, and a custom RF communication protocol, with MAVLink support for telemetry and ground station integration.",
  "microfpv_title": "Micro FPV Drone",
  "microfpv_p1": "Fully custom build that fits in the palm of your hand. All structural components designed in CAD, including the frame, camera mount, antenna mount, and battery mount, all 3D-printed and iterated across multiple revisions. Both 3D-printed and carbon-fiber variants are viable at this scale; the production build uses a carbon fiber frame machined by fabrication partners. Evaluated both custom multi-board PCB designs and off-the-shelf AIO boards that integrate FC, RF, ESC, and VTX on a single board, with the AIO approach providing meaningful size savings. Firmware stack primarily uses Betaflight and custom firmware, with additional support for ArduPilot and iNav. Tested indoors and outdoors, capable of agile tight-space flight and stable outdoor operation. Equipped with FPV camera and live video.",
  "uavcontroller_title": "UAV Controller",
  "uavcontroller_p1": "A full quadcopter flight control stack covering controllers, path planning, safety, and simulation, built on ROS 2. It runs on top of any flight controller firmware (Betaflight, ArduPilot, iNav, or custom) through standard CRSF/SBUS/PPM links. The stack supports both GPS-based navigation and GPS-denied operation using optical flow and range finder data.",
  "uavcontroller_li1": "Controllers (multiple options): cascaded PID, LQR, MPC (C++ for ROS; Python for standalone sim)",
  "uavcontroller_li2": "ROS 2 simulation workflow: Gazebo + RViz for system integration, visualization, and controller testing",
  "uavcontroller_li3": "Path planning (multiple options): A*, RRT, RRT* across plain, forest, and mountain terrains; fully adjustable via config",
  "uavcontroller_li4": "Safety gate: validation, limiting, watchdog",
  "uavcontroller_li5": "TX/RX stack: ESP32 (ESP-NOW) for indoor testing; outdoor comms use LoRa (ELRS), plus two custom stacks on 2.4 GHz and 433 MHz; CRSF/SBUS/PPM bridging; GPS support for autonomous navigation",
  "uavcontroller_li6": "Standalone Python-based simulator for fast iteration without ROS: quad pose visualization, dynamics simulation, and interchangeable controller/path-planner modules",
  "uavcontroller_video_caption": "GPS-denied hovering and landing using sensor fusion between IMU, barometer, rangefinder, and optical flow.",
  "uavcontroller_forest_caption": "Forest terrain simulation - path planning through dense environments",
  "uavcontroller_gazebo_caption": "Gazebo simulation - RViz visualization and controller testing",
  "uavcontroller_planner_caption": "Standalone Python simulator - RRT* path planning over 3D terrain",
  "uavcontroller_drone_caption": "5\" drone build used to test custom TX/RX communication stacks",
  "uavcontroller_mountain_caption": "RotorPy integration - RRT* planning with full quadrotor dynamics",
  "esp32lidar_title": "ESP32 LiDAR Bot",
  "esp32lidar_p1": "ESP32-C3 mobile robot with two DC motors, a motor driver, and a 360° LiDAR. Modes include manual teleop, LiDAR-based wander, mapping, and obstacle avoidance.",
  "esp32lidar_p2": "A browser interface renders the live LiDAR point cloud. Repo also keeps V1 — the original WiFi / ESP-NOW browser-controlled RC car with differential and omni drive variants.",
  "esp32lidar_p3": "Deployed as a target bot for a lab evaluation where students programmed their robots to intercept it — when I was a TA for a mechatronic systems course.",
  "gearbox_title": "Wolfrom Bilateral Gearbox Actuator",
  "gearbox_p1": "A compound Wolfrom bilateral gearbox with high reduction ratio and meaningful backdrivability, fabricated entirely on a desktop FDM 3D printer. Useful for robotic arm joints, legged actuators, and force-controlled manipulation.",
  "gearbox_p2": "Based on my published research paper, where I co-optimized gearbox design parameters by combining Taguchi Orthogonal Arrays with Bayesian Optimization. One configuration identified through this method — 63.6:1 reduction ratio, backdrivable under 0.35 Nm, 49% score improvement over the Taguchi baseline.",
  "manualracer_title": "Wyvern MK1 — High-Speed FPV Drone",
  "manualracer_p1": "First-generation Wyvern drone, a 3.5\" quadcopter built for freestyle and racing. Equipped with 1960KV brushless motors and running on 6S, it is capable of speeds exceeding 100 mph (160 km/h). Manual flight is the core; GPS-based rescue on failsafe is a secondary addition. Typically runs 4S or 6S (3S minimum). Powered by an STM32F722 flight controller running Betaflight or iNav; the onboard flash memory is insufficient for ArduPilot or PX4. 2.4GHz ELRS for control and 5.8GHz analog FPV for video.",
  "manualracer_p2": "Frame designed using topology optimization (Generative Design, Fusion 360). Iterated across multiple materials and processes - laser cutting, 3D printing (ABS, PA, PC, CF) - with flight controller blackbox logs validating vibration and structural performance at each step. Final frame: CNC carbon fiber. TPU 3D-printed mounts for antenna and camera. Full FPV with live video.",
  "mk1_protocad_caption": "Wyvern MK1 - prototype CAD",
  "mk1_cad_caption": "Wyvern MK1 - CAD",
  "mk1_protobuild_caption": "Wyvern MK1 - prototype",
  "mk1_build1_caption": "Wyvern MK1 - build",
  "mk1_build2_caption": "Wyvern MK1 - build",
  "7dof_title": "7 DOF Robot Arm",
  "7dof_p1": "Panda Franka 7 DOF arm. Robotic manipulation system for pick-and-place operations. Path planning: RRT and potential field—reach the goal while avoiding collisions and obstacles. Forward and inverse kinematics; vision-based object detection.",
  "diffdrive_title": "Differential-Drive Mobile Robot",
  "diffdrive_p1": "Semi-autonomous mobile robot with web interface. Features: localization-based navigation, wall follow, manual control for target tracking. PID control via motor encoders; position/orientation from Vive tracker integration. RGB LED effects and wheel system live visual feedback. Web-based control: point somewhere, the robot goes. Main board ESP32 for wireless; multiple microcontroller boards.",
  "rldrone_title": "RL Racing Drone",
  "rldrone_p1": "Sim-to-real reinforcement learning control stack for quadrotors. End-to-end system to deploy PyTorch RL policies on real hardware using ROS 2, Betaflight MSP, and ESP32 (CRSF/RC override). Designed for real-world deployment: deterministic control paths, explicit authority handoff, hardware-enforced safety, recoverable failure modes. RL inference on onboard SBC; ROS 2 as control/safety layer; ESP32 enforces RC-side arming and AUX; physical kill always overrides software. FPV not yet equipped.",
  "esp32fc_title": "Nori AIO - Custom ESP32 Flight Controller (PCB)",
  "esp32fc_p1": "Custom PCB designed in Altium Designer — a breakout-style all-in-one board for ESP32 with motor drivers integrated, enabling full flight control on a single chip. \"Nori AIO\" stands for Nori (this site) and AIO (all-in-one). This is the ESP32-based prototype, which isn't supported by mainstream firmware, so I wrote my own.",
  "additional_title": "Additional Projects",
  "note_milkv_title": "Custom Embedded Linux Platform — Milk-V Duo S",
  "note_milkv_p": "Board bringup, custom toolchain, and build pipeline for the Milk-V Duo S (RISC-V/ARM64 SBC) for lab swarm robotics research. Built a ROS 2 / CycloneDDS bridge so the boards - too constrained for ROS 2 - can communicate with a centralized PC that publishes and subscribes over standard ROS 2. Core platform is in a private lab repo; an earlier Ubuntu port is public. <a href=\"https://github.com/RawFish69/ubuntu-milkv-duos\" target=\"_blank\" rel=\"noopener\">Ubuntu Port Repo</a>",
  "note_fpvsim_title": "FPV Drone Simulator",
  "note_fpvsim_p": "Browser-based FPV trainer built with Three.js. Twin-stick controls (WASD + mouse or IJKL), acro and angle flight modes, adjustable drone profiles, and multiple weather/lighting environments. <a href=\"https://nori.fish/demo/fpv\" target=\"_blank\" rel=\"noopener\">Open Demo</a>",
  "note_pid_title": "PID Controller Visualizer",
  "note_pid_p": "Interactive browser demo of cascaded PID loops for altitude and pitch control. Tune P/I/D gains live, switch between step/sine/square setpoints, inject wind gusts, and observe overshoot and integral windup in real time. <a href=\"https://nori.fish/demo/pid\" target=\"_blank\" rel=\"noopener\">Open Demo</a>",
  "note_earlystage_title": "Early-Stage UAV Variants",
  "note_earlystage_p": "Several early-stage quadcopter builds, each exploring a different approach to flight control from the ground up—rather than relying on off-the-shelf flight controllers or plug-and-play stacks. One of them (pictured) was built on perfboard with an ESP32-C3, 4 MOSFETs, and an IMU driving 4 brushed DC motors, running a PID loop in Arduino to stabilize from raw IMU data. For anyone who truly wants to understand how a system works, it is better to build it from first principles than to reach for a pre-made solution.",
  "note_uavtools_title": "UAV Testing Tools",
  "note_uavtools_p": "A suite of tools built around UAV development and testing. Includes a custom test rig for securing drones during static thrust runs, flight controller software, GPS module software with calibration tooling, a gesture-based test controller—an IMU and RF transceiver mounted on a handheld board that lets you fly the drone with hand movements—testing scripts, and a web-based drone movement simulator that was later superseded by the ROS 2 simulation stack in the UAV controller project.",
  "note_gripper_title": "Mechanical Gripper",
  "note_gripper_p": "Physical build of my <a href=\"https://nori.fish/demo/claw3d/\" target=\"_blank\" rel=\"noopener\">claw machine simulator</a>.",
  "note_rangefinder_title": "Range Finder Tools",
  "note_rangefinder_p": "Built multiple distance-sensing tools using ToF and ultrasonic sensors for calibration, validation, and rapid integration tests.",
  "note_toaste_title": "Thermal Sensor Mobile Bot (Toast-E)",
  "note_toaste_p": "Differential-drive robot with thermal imaging streamed to a web browser. ESP32-based; uses ESP-NOW for wireless joystick control and AMG8833 8×8 thermal sensor. Live heatmap view with bilinear interpolation upscaling (64×64) for smoother visualization. <a href=\"https://github.com/RawFish69/Toast-E\" target=\"_blank\" rel=\"noopener\">GitHub Repo</a>",
  "link_github": "GitHub Repo",
  "link_back_home": "Home",
  "link_back": "← Back to Home",
};

const zh = {
  "page_title": "个人项目集",
  "page_intro": "无人系统 · 机电一体化 · 全栈工程",
  "contact_label": "联系邮箱:",
  "nav_toggle_show": "▼ 项目目录",
  "nav_toggle_hide": "▲ 项目目录",
  "nav_mk3": "Wyvern MK3 — FPV四旋翼",
  "nav_long_range": "Wyvern MK2 — 远航无人机",
  "nav_nori_f411": "Nori F411 飞控板",
  "nav_micro_fpv": "微型FPV无人机",
  "nav_uav_controller": "无人机控制器",
  "nav_esp32_lidar": "激光雷达小车",
  "nav_gearbox": "Wolfrom 双侧齿轮箱",
  "nav_manual_racer": "Wyvern MK1 — 竞速无人机",
  "nav_7dof": "Franka机械臂控制",
  "nav_diff_drive": "差速驱动移动机器人",
  "nav_rl_drone": "强化学习竞速无人机",
  "nav_esp32_fc": "ESP32 飞控板",
  "mk3_title": "Wyvern MK3 - 自主FPV四旋翼",
  "mk3_p1": "第三代 Wyvern 无人机，一台3寸FPV四旋翼。硬件设计、固件、射频通信及嵌入式飞控均在前代基础上迭代开发，同时也测试过市售方案。MK3 集成了两条路径的经验。",
  "mk3_p2": "MK3 有两个版本：一个为 cruise/FPV 通用版，另一个为自主飞行版（GPS 及 GPS 拒止环境，使用光流、测距仪、IMU、气压计、磁罗盘等）。自主飞行基于 ArduPilot、PX4 及自研固件 - 支持高度/位置保持、悬停、GPS 航点。支持 1104 至 1505 电机，2S 锂离子至 6S 锂聚合物电池。CNC 碳纤维机架，TPU 打印结构件。兼容 DJI O4 Lite/Pro。",
  "mk3_video_caption": "飞行机动与高空巡航。",
  "mk3_o4_video_caption": "飞行机动与高空巡航 (O4 Lite)。",
  "mk3_rescue_video_caption": "自主救援与返航 (O4 Pro)。",
  "mk3_render_caption": "Wyvern MK3 - CAD 渲染",
  "mk3_proto1_caption": "Wyvern MK3 - 原型机",
  "mk3_build1_caption": "Wyvern MK3 - 成品机",
  "mk3_cad_caption": "Wyvern MK3 - CAD",
  "mk3_proto2_caption": "Wyvern MK3 - 原型机",
  "mk3_build2_caption": "Wyvern MK3 - 成品机",
  "mk3_auto1_caption": "Wyvern MK3 - 自主飞行版",
  "longrange_title": "Wyvern MK2 — 远航无人机",
  "longrange_p1": "自主设计并迭代了多版3.5寸四旋翼，涵盖机械设计、PCB设计、嵌入式开发、加工组装与结构集成。碳纤维机架由外协加工，所有安装件及集成部件均为自行设计并3D打印。配备完整FPV系统及实时图传。",
  "longrange_p2": "采用1–2S 18650锂离子电池供电，整机重量低于250克，搭载1202.5无刷电机，续航20–25分钟。固件栈以Betaflight为主，同时在自定义固件、iNav及ArduPilot配置上均有额外支持与测试。集成GPS，支持航点飞行及GPS救援/安全返航功能。",
  "longrange_video_caption": "定高悬停旋转环视周围环境，随后沿河面巡航。",
  "norif411_title": "Nori F411 - 飞控板PCB",
  "norif411_p1": "基于Altium Designer设计的飞控PCB，主控STM32F411，板载MPU6050 IMU提供陀螺仪及加速度计数据。为该板自主移植Betaflight固件，飞控核心代码源自<a href=\"#proj-uav-controller\">无人机控制器项目</a>。",
  "norif411_p2": "支持 ELRS、TBS Crossfire 及自研 RF 通信链路，并兼容 MAVLink 遥测与地面站通信协议。",
  "microfpv_title": "微型FPV无人机",
  "microfpv_p1": "掌心大小，完全自主设计。所有结构件均在CAD中完成，包括机架、摄像头座、天线座、电池座，全部3D打印并历经多版迭代。此尺度下3D打印与碳纤维方案均可行，量产版本采用外协加工的碳纤维机架。评估了两种方案：自行设计的多板PCB，以及集飞控、射频、电调、图传于一板的市售AIO方案——AIO在尺寸上优势显著。固件栈以Betaflight及自定义固件为主，同时支持ArduPilot与iNav。经室内外测试，既可在狭小空间内灵活飞行，也能稳定户外运行。配备FPV摄像头及实时图传。",
  "uavcontroller_title": "无人机控制器",
  "uavcontroller_p1": "一套完整的四旋翼飞行控制栈，涵盖控制器、路径规划、安全机制与仿真，基于 ROS 2 构建。可通过标准的 CRSF/SBUS/PPM 链路运行在任意飞控固件之上（Betaflight、ArduPilot、iNav 或自研固件）。该控制栈同时支持基于 GPS 的导航，以及基于光流和测距仪数据的 GPS 拒止环境飞行。",
  "uavcontroller_li1": "控制器（多种方案）：级联 PID、LQR、MPC（ROS 中采用 C++，独立仿真采用 Python）",
  "uavcontroller_li2": "ROS 2 仿真流程：Gazebo + RViz，用于系统集成、可视化及控制器测试",
  "uavcontroller_li3": "路径规划（多种方案）：A*、RRT、RRT*，支持平地、林地、山地地形，全参数可调",
  "uavcontroller_li4": "安全机制：数据校验、限幅、看门狗",
  "uavcontroller_li5": "通信链路：室内采用 ESP32（ESP-NOW），室外采用 LoRa（ELRS），以及两套自研链路（2.4 GHz 与 433 MHz）；支持 CRSF/SBUS/PPM 桥接；GPS 支持自主导航",
  "uavcontroller_li6": "独立 Python 仿真器，无需 ROS 即可快速迭代：无人机姿态可视化、动力学仿真、可插拔的控制器/路径规划模块",
  "uavcontroller_video_caption": "通过融合 IMU、气压计、测距传感器和光流传感器，实现无 GPS 环境下的悬停与降落。",
  "uavcontroller_forest_caption": "森林地形仿真 - 密集环境下的路径规划",
  "uavcontroller_gazebo_caption": "Gazebo 仿真 - RViz 可视化与控制器测试",
  "uavcontroller_planner_caption": "独立 Python 仿真器 - 在三维地形上进行 RRT* 路径规划",
  "uavcontroller_drone_caption": "用于测试自研通信链路的 5 寸无人机",
  "uavcontroller_mountain_caption": "RotorPy 集成 - 结合完整四旋翼动力学的 RRT* 规划",
  "esp32lidar_title": "ESP32 激光雷达小车",
  "esp32lidar_p1": "基于ESP32-C3的移动机器人，搭载双直流电机、电机驱动及360°激光雷达。支持手动遥控、雷达漫游、建图、避障等模式。",
  "esp32lidar_p2": "浏览器端可实时渲染激光雷达点云。仓库同时保留V1版本 —— 最初基于WiFi/ESP-NOW的浏览器遥控RC车，含差速及全向驱动两种构型。",
  "esp32lidar_p3": "曾用于一门机电一体化课程的实验环节 —— 当时我担任助教，学生需要编程让他们的机器人拦截这台小车。",
  "gearbox_title": "Wolfrom 双侧齿轮箱执行器",
  "gearbox_p1": "复合Wolfrom双侧齿轮箱，兼具高减速比与可反向驱动特性，整机采用桌面级FDM 3D打印机制造。适用于机械臂关节、足式机器人执行器及力控操作。",
  "gearbox_p2": "基于本人已发表论文，采用田口正交表与贝叶斯优化联合优化减速箱设计参数。优化所得配置之一 —— 减速比63.6:1，0.35 Nm以下可反向驱动，综合评分较田口基线提升49%。",
  "manualracer_title": "Wyvern MK1 — 高速FPV无人机",
  "manualracer_p1": "第一代 Wyvern 无人机，一台面向花式飞行与竞速的 3.5 英寸四旋翼。搭载 1960KV 无刷电机并采用 6S 供电，最高速度可超过 100 mph（160 km/h）。以手动飞行为核心，GPS 救援作为辅助安全功能。通常使用 4S 或 6S 电池（最低支持 3S）。搭载 STM32F722 飞控，运行 Betaflight 或 iNav；受板载闪存容量限制，无法运行 ArduPilot 或 PX4。采用 2.4GHz ELRS 遥控链路和 5.8GHz 模拟图传系统。",
  "manualracer_p2": "机架采用 Fusion 360 拓扑优化（衍生式设计）完成。经过多种材料与工艺迭代 - 激光切割、3D 打印（ABS、PA、PC、CF）- 每版均通过飞控黑匣子数据验证振动与结构性能。最终版本采用 CNC 碳纤维机架。TPU 3D 打印天线座与摄像头座。配备完整 FPV 系统及实时图传。",
  "mk1_cad_caption": "Wyvern MK1 - 成品CAD",
  "mk1_protocad_caption": "Wyvern MK1 - 原型CAD",
  "mk1_protobuild_caption": "Wyvern MK1 - 原型机",
  "mk1_build1_caption": "Wyvern MK1 - 成品机",
  "mk1_build2_caption": "Wyvern MK1 - 成品机",
  "7dof_title": "七自由度机械臂",
  "7dof_p1": "Panda Franka七自由度机械臂。面向抓取放置操作的机器人系统。路径规划采用RRT与势场法 —— 在避障前提下到达目标点。支持正逆运动学及基于视觉的目标检测。",
  "diffdrive_title": "差速驱动移动机器人",
  "diffdrive_p1": "半自主移动机器人，提供Web控制界面。功能包括：基于定位的导航、沿墙行走、手动目标跟踪。PID控制基于电机编码器闭环；位置/姿态通过Vive追踪器获取。配备RGB LED状态指示及车轮系统实时视觉反馈。Web控制方式为点选目标位置。主控采用ESP32实现无线通信，多块微控制器协同工作。",
  "rldrone_title": "强化学习竞速无人机",
  "rldrone_p1": "面向无人机的仿真到实际迁移强化学习控制栈。端到端系统，通过ROS 2、Betaflight MSP及ESP32（CRSF/RC覆盖）将PyTorch RL策略部署至真实硬件。面向实际部署设计：确定性控制路径、明确的权限交接、硬件级安全约束、可恢复的故障模式。RL推理运行于机载SBC，ROS 2作为控制/安全层，ESP32负责遥控端解锁及AUX通道管理，物理急停优先级始终高于软件。暂未配备FPV。",
  "esp32fc_title": "Nori AIO —— 自制ESP32飞控板",
  "esp32fc_p1": "基于Altium Designer自主设计的PCB —— 面向ESP32的扩展式AIO板，集成电机驱动，单芯片实现完整飞控。命名Nori AIO取自本网站名与All-In-One。主流固件生态尚未支持ESP32飞控方案，故自行完成固件开发。",
  "additional_title": "其他项目",
  "note_milkv_title": "自建嵌入式Linux平台 —— Milk-V Duo S",
  "note_milkv_p": "为实验室集群机器人研究完成Milk-V Duo S（RISC-V/ARM64 SBC）板级移植，包含自建工具链及编译流水线。开发了ROS 2 / CycloneDDS桥接层，使资源受限、无法运行完整ROS 2的板卡能够与中心PC（负责收发标准ROS 2消息）通信。核心代码托管于实验室私有仓库，早期Ubuntu移植版本已公开。 <a href=\"https://github.com/RawFish69/ubuntu-milkv-duos\" target=\"_blank\" rel=\"noopener\">公开仓库</a>",
  "note_fpvsim_title": "FPV无人机模拟器",
  "note_fpvsim_p": "基于Three.js的浏览器端FPV训练器。支持双摇杆控制（WASD+鼠标 或 IJKL）、特技模式与角度模式、可调无人机参数，以及多种天气/光照环境。 <a href=\"https://nori.fish/demo/fpv\" target=\"_blank\" rel=\"noopener\">在线演示</a>",
  "note_pid_title": "PID控制器可视化工具",
  "note_pid_p": "浏览器端交互式演示，展示面向高度及俯仰控制的级联PID回路。支持实时调节P/I/D增益、切换阶跃/正弦/方波设定值、注入风扰扰动，并实时观察超调及积分饱和现象。 <a href=\"https://nori.fish/demo/pid\" target=\"_blank\" rel=\"noopener\">在线演示</a>",
  "note_earlystage_title": "早期无人机方案",
  "note_earlystage_p": "若干早期无人机设计方案，每套方案均探索了从零构建飞行控制的不同技术路径 —— 而非直接采用市售飞控或集成方案。其中一套（如图）基于洞洞板，采用ESP32-C3、4个MOSFET及IMU驱动4个有刷直流电机，运行Arduino下的PID循环，基于原始IMU数据进行姿态增稳。从第一性原理出发理解系统，较直接采用现成方案更具价值。",
  "note_uavtools_title": "无人机测试工具集",
  "note_uavtools_p": "围绕无人机开发与测试构建的工具集。包含：静态推力测试专用固定台架、飞控软件、带校准工具的GPS模块软件、基于手势的测试控制器（IMU及射频模块集成于手持板卡，通过手势控制飞行器）、测试脚本，以及一套网页端无人机运动模拟器（后被无人机控制器项目中的ROS 2仿真栈取代）。",
  "note_gripper_title": "机械爪",
  "note_gripper_p": "我的<a href=\"https://nori.fish/demo/claw3d/\" target=\"_blank\" rel=\"noopener\">抓娃娃机模拟器</a>实体版本。",
  "note_rangefinder_title": "测距工具集",
  "note_rangefinder_p": "基于ToF及超声波传感器构建的多套距离测量工具，用于校准、验证及快速集成测试。",
  "note_toaste_title": "热成像移动机器人 (Toast-E)",
  "note_toaste_p": "差速驱动机器人，支持热成像画面实时推送至浏览器端。基于ESP32平台，采用ESP-NOW实现无线摇杆控制，搭载AMG8833 8×8热传感器。浏览器端提供实时热力图视图，采用双线性插值上采样至64×64，实现更平滑的可视化效果。 <a href=\"https://github.com/RawFish69/Toast-E\" target=\"_blank\" rel=\"noopener\">GitHub 仓库</a>",
  "link_github": "GitHub 仓库",
  "link_back_home": "首页",
  "link_back": "← 返回首页",
};

const translations = { en, zh };

function toggleQuickNav() {
  const nav = document.getElementById('robotics-quicknav');
  const btn = document.getElementById('quicknav-toggle');
  if (!nav || !btn) return;
  const isOpen = nav.classList.toggle('nav-open');
  const lang = localStorage.getItem('nori-lang') || 'en';
  const data = translations[lang] || translations.en;
  btn.textContent = data[isOpen ? 'nav_toggle_hide' : 'nav_toggle_show'];
}

function layoutQuickNav() {
  const nav = document.querySelector('.robotics-quicknav');
  if (!nav) return;
  const items = nav.querySelectorAll('a');
  const n = items.length;
  let cols = 5;
  for (let d = 5; d >= 2; d--) {
    if (n % d === 0) { cols = d; break; }
  }
  const pct = (100 / cols) + '%';
  items.forEach(a => { a.style.flex = `0 0 ${pct}`; });
}

function setLang(lang) {
  const data = translations[lang] || translations.en;
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (data[key] !== undefined) el.innerHTML = data[key];
  });
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.lang === lang);
  });
  localStorage.setItem('nori-lang', lang);
  document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en';
  layoutQuickNav();
  const btn = document.getElementById('quicknav-toggle');
  if (btn) {
    const nav = document.getElementById('robotics-quicknav');
    const isOpen = nav && nav.classList.contains('nav-open');
    btn.textContent = data[isOpen ? 'nav_toggle_hide' : 'nav_toggle_show'];
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const saved = localStorage.getItem('nori-lang');
  const detected = navigator.language?.startsWith('zh') ? 'zh' : 'en';
  setLang(saved || detected);
});
