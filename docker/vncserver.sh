#!/bin/bash

[ -z $VNCPASSWORD ] && { echo "specify -e VNCPASSWORD=secret"; exit 1;}

#cleanup tmp from previous run
rm -rf /tmp/.X*
rm -rf /tmp/.x*
rm -rf /tmp/ssh*

#set vncserver password
mkdir /root/.vnc 2>/dev/null
echo $VNCPASSWORD | vncpasswd -f > /root/.vnc/passwd 
chmod 0600 /root/.vnc/passwd

#vncserver startup script
#run gr-perf-monitorx only when port 9090 is open
#(indicates that gnuradio is started)
cat >> /root/.vnc/xstartup  << 'EOF'
#!/bin/bash
xrdb /root/.Xresources
startxfce4 &
until netstat -natp | grep 9090
do
  sleep 1
done
/usr/local/bin/gr-perf-monitorx &
EOF
chmod +x /root/.vnc/xstartup

# suppress xfce panel message about first start
cp /etc/xdg/xfce4/panel/default.xml \
/etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml

#create menu entry for gr-monitor
mkdir -p /root/.local/share/applications/
cat >> /root/.local/share/applications/gr-ctrlport-monitor.desktop  << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Encoding=UTF-8
Exec=/usr/local/bin/gr-perf-monitorx
StartupNotify=false
Categories=X-XFCE;X-Xfce-Toplevel;
OnlyShowIn=XFCE;
Comment=GnuRadio monitor
Name=GnuRadio monitor
EOF

#start vncserver with bigger resolution (increase user experience)
USER=root vncserver -geometry 1600x1200
