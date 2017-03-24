"""
Script for defining new commands inside Wing IDE.
"""

import ctypes
import os
import subprocess
import sys
import shutil
import re
import time

import wingapi

def _copy_files_to_pi( robot_filename ):
	# Look in robot.py for GRIP_FILE_PATH
	vision_dir = None
	
	for line in open( robot_filename, 'r' ).readlines( ):
		if line.startswith( "RPI_VISION_DIR" ):
			vision_dir_base = line.split( "=" )[ -1 ].strip().lstrip('r').strip('"')
			print( 'RPI_VISION_DIR =', vision_dir_base )
			vision_dir = os.path.join( os.path.dirname( robot_filename ), vision_dir_base )
			break

	if not vision_dir:
		print( 'RPI_VISION_DIR not defined, skipping RPi file copy.')
		return

	if not os.path.exists( vision_dir ):
		print( 'RPI_VISION_DIR "{0}" not found!'.format( vision_dir ) )
		return

	# Copy entire vision folder over
	if not os.path.exists( vision_dir ):
		print( 'No "vision" dir found, skipping copy' )
		return
	
	print( 'Copying folder to RPi: "{0}"'.format( vision_dir ) ) 
	result = subprocess.Popen( 'pscp.exe -r -pw UndeadRobotics "{0}" ctrlz@10.40.96.18:/home/ctrlz'.format( vision_dir ) ).wait( )
	print( 'delay...')
	time.sleep( 0 )


def _handle_process_output( proc ):	
	"""
	This runs the deploy/sim process and checks for errors, raising a messagebox
	if any exceptions are hit.
	"""
	stdout_data, stderr_data = proc.communicate( )

	if not stderr_data:
		# Things are working fine
		return

	# Prep the stderr message
	lines = stderr_data.split( '\n' )
	idx1 = 0
	for line in lines:
		if line.startswith( 'Traceback' ):
			break
		idx1 += 1

	idx2 = 0
	for line in lines:
		if line.startswith( 'Locals' ):
			break
		idx2 += 1

	msg = '\n'.join( lines[ idx1:idx2 ] )

	ctypes.windll.user32.MessageBoxA( 0, 'Robot code error!\n---\n{0}'.format( msg ), 'Robot Code Error', 1 )


def roborio_run_simulation( ):
	app = wingapi.gApplication
	robot_filename = app.GetProject( ).GetMainDebugFile( )

	if not robot_filename:
		return

	# Kill existing netconsole processes
	result = subprocess.Popen( 'taskkill.exe /F /IM python.exe', shell = True ).wait( )

	# Save all docs first
	wingapi.gApplication.ExecuteCommand( 'save-all' )

	#_copy_grip_file_to_pi( robot_filename )
	
	proc = subprocess.Popen( 'py.exe "{0}" sim'.format( robot_filename ), stdout = subprocess.PIPE, stderr = subprocess.PIPE )

	_handle_process_output( proc )


def roborio_deploy_and_run( ):
	app = wingapi.gApplication
	robot_filename = app.GetProject( ).GetMainDebugFile( )

	if not robot_filename:
		return

	# Kill existing netconsole processes
	result = subprocess.Popen( 'taskkill.exe /F /IM python.exe', shell = True ).wait( )

	# Save all docs first
	wingapi.gApplication.ExecuteCommand( 'save-all' )

	_copy_files_to_pi( robot_filename )

	proc = subprocess.Popen( 'py.exe "{0}" deploy --nc --skip-tests --no-version-check'.format( robot_filename ) )
