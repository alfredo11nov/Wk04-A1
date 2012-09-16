/**
this is my second basic font for F
forked from DIDNY font 3
*/

void setup()
{ size (400,400);
frameRate(30);
//string portName = "COM4";
}


void draw()
{
  
background (200-mouseY/3);
fill (0);

int x = 75;
int x2 = 150;
int y;
int t1 = (100+mouseX/2); // length of top part
int t2 = (100+mouseX/2); // length of top part
int randomness = mouseX;

rect(x,50,75, 300);

for(y = 50; y <= 400; y = y + 1 ){
 if(y < 150){
   line(x*2,y,t1 + random(randomness),y);
 }

 else if((y >= 180) && (y < 230)){
   line(x*2,y,t2 + random(randomness/2),y);
 }
 
 
}
}

