

proc __load_var {imgdir extension} {
	variable I
	foreach file [glob -directory $imgdir $extension] {
		set img [file tail [file rootname $file]]
		set code [catch {
    		set I($img) [image create photo -file $file -format png]
		} result]
		if {$code == 1} {puts $result}	
	}
}


proc load_local_dir {{extension *.png}} {
	variable directory
	set directory [file dirname [info script]]

	__load_var $directory $extension

	#return $I
}


proc get_images {} {
	global I

	foreach {key value} [array get I] {
		append tempstring "'" $key "', "
	}

	set tempstring [string trim $tempstring ", "]

	return "\[${tempstring}\]"
}

proc load_image {filename {key ""} {format png}} {
	variable img

	if {$key != ""} {
		set img $key
	} else {
		set img [file tail [file rootname $filename]]
	}

	set I($img) [image create photo -file $filename -format $format]
}


proc load_dir {dirname {path ""} {extension *.png}} {
	variable directory
	if {$path == ""} {
		set directory [file join [file dirname [info script]] $dirname]
	} else {
		set directory [file join $path $dirname]
	}

	__load_var $directory $extension
}