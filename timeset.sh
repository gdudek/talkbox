echo "Setting TimeZone..."
export tz=`wget -qO - http://geoip.ubuntu.com/lookup | sed -n -e 's/.*<TimeZone>\(.*\)<\/TimeZone>.*/\1/p'` 
if test "x$tz" = x
    then
    echo Cannot get time zone. Leaveing it `cat /etc/timezone`
else
	if test "$tz" = "America/Rainy_River"
	then
	export tz="America/Montreal"
	fi    
	echo $tz > /etc/timezone
	# if we used timedatectl
	# timedatectl set-timezone $tz
	# export tz=`timedatectl status| grep Timezone | awk '{print $2}'`
	dpkg-reconfigure -f noninteractive tzdata
        echo "TimeZone set to $tz"
fi
