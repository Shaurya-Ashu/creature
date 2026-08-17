# creature
It's a quadruple robot build around raspberry pi 4B (8gb) variant . It has a total of 8 dof and can perform so many poses for now .

# Zine 
<img width="540" height="828" alt="Frame 9" src="https://github.com/user-attachments/assets/7caea4d4-3988-4db2-9473-0d48096bbec2" />

# Demo 
  https://youtu.be/hGYGTCDXikk?si=BeiIlC8ztwMHXgLd
  
# Why I built it 
I have build it to make a base platform for future projects like we wold add lidar , cameras , IMU and many more sensors and even make it run autonomously like using ros2 locally on the pi etc .

# Build 
So I have firstly designed it in fusion then printed the legs and servo joints and cute out the base plate with some foam sheet and reinforced it with acrylic sheet pieces , then I just hot glued them together and tested them.

I have assigned every servo there respected name as given in the img below  :-

<img width="2775" height="3133" alt="WhatsApp Image 2026-08-17 at 12 18 25" src="https://github.com/user-attachments/assets/4edb25d1-3f04-4528-83e7-49952b81a58a" />


# schematics 
It's the most simplest circuit I have made so far

<img width="840" height="369" alt="Screenshot 2026-08-17 at 10 02 52 PM" src="https://github.com/user-attachments/assets/8bb40b95-fcd8-4640-ad6e-c57ce7b43edc" />

It follows :
FL1 --> GPIO 6
FL2 --> GPIO 26
FR1 --> GPIO 13
FR2 --> GPIO 5
BL1 --> GPIO 22
BL2 --> GPIO 27
BR1 --> GPIO 4
BR2 --> GPIO 17

and there is a LM7805 LDO to regulate the voltage of the battery pack 

# PCB 
I have designed one for you guys in easyEDA but I have build it on a perfboard .

<img width="551" height="475" alt="Screenshot 2026-08-17 at 10 01 26 PM" src="https://github.com/user-attachments/assets/4e9f58d5-0410-4549-89ac-cf4734dd8e51" />

<img width="557" height="478" alt="Screenshot 2026-08-17 at 10 01 36 PM" src="https://github.com/user-attachments/assets/4fda7326-8def-4787-a04f-a3a5727110ba" />

<img width="964" height="1280" alt="WhatsApp Image 2026-08-17 at 12 18 21" src="https://github.com/user-attachments/assets/3995d346-c6dc-4730-8e0e-4b8eeabdf790" />

# poses
It can perform many poses some of them are given below:
Handstand
<img width="1200" height="1600" alt="WhatsApp Image 2026-08-17 at 13 04 53" src="https://github.com/user-attachments/assets/8c92b324-7966-4cb5-839a-df4d80b1f59a" />

Sitting like a Dog
<img width="4096" height="3072" alt="WhatsApp Image 2026-08-17 at 12 34 18 (1)" src="https://github.com/user-attachments/assets/038b39de-b1c3-4e3c-bf56-ba24a38a9d82" />

Bow Down to you 
<img width="4096" height="3072" alt="WhatsApp Image 2026-08-17 at 12 34 22" src="https://github.com/user-attachments/assets/474799bb-bcf8-4f08-8138-d8564babcc7b" />

Says Hi/Bye 
<img width="4096" height="3072" alt="WhatsApp Image 2026-08-17 at 12 34 24" src="https://github.com/user-attachments/assets/caf87ade-006c-403c-bcf0-5f14c55caf78" />

RIP
<img width="4096" height="3072" alt="WhatsApp Image 2026-08-17 at 12 34 18" src="https://github.com/user-attachments/assets/004610a4-e50f-484f-b2fe-9163cde84a21" />


# Firmware 
 I have tried everything from inverse kinematics to hardcoded but it can't move due to the limited traction between the legs and the floor , In future will work on an alternative design for it, but for now it can perform many poses which are mentioned above . 
 The following zip file contain configuration file so you could configure your server motors to the limitations of rotation and then after that you can use a GUI file to create your custom patterns and movements.

 please download pigpio on you raspberry pi 

