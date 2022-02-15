echo OFF

echo Removing dist ...
CMAKE -E rm -rf dist
echo DONE

echo Removing egg-info  ...
CMAKE -E rm -rf src/cemake.egg-info
echo DONE
