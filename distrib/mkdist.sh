#!/bin/bash
#
#  Create an end-user distribution of Labtainers.
#  This uses git archive, basing the distribution on committed content of the 
#  current branch of the local repo.
#  use -t to force test registry
#  use -r to update release distribution
#
function contains() {
    local n=$#
    local value=${!n}
    for ((i=1;i < $#;i++)) {
        if [ "${!i}" == "${value}" ]; then
            echo "y"
            return 0
        fi
    }
    echo "n"
    return 1
}
commit=`git describe --always`
revision=`git tag`
skip="skip-labs"
skiplist=""
lines=`cat $skip`
for line in $lines; do
    lab=$(basename $line)
    skiplist+=($lab)
done
mkdir -p /tmp/labtainer_pdf_$USER
here=`pwd`
cd ../
rootdir=`pwd`
ddir=$(mktemp -d -t labtainer-distrib-XXXXXXXX)
ldir=$ddir/labtainer
ltrunk=$ldir/trunk
scripts=$ltrunk/scripts
labs=$ltrunk/labs
docs=$ltrunk/docs
rm -fr /$ddir
mkdir $ddir
mkdir $ldir
mkdir $ltrunk
branch=$(git rev-parse --abbrev-ref HEAD)
if [[ "$1" != "-t" ]]; then
    registry=$(scripts/labtainer-student/bin/registry.py)
    echo "Make distribution from branch: $branch  registry: $registry"
else
    echo "Make distribution from branch: $branch  Using premaster registry OVERRIDE"
fi
git archive $branch README.md | tar -x -C $ltrunk
#git archive $branch | tar -x -C $ltrunk
sed -i "s/mm\/dd\/yyyy/$(date '+%m\/%d\/%Y %H:%M')/" $ltrunk/README.md
sed -i "s/^Revision:/Revision: $revision/" $ltrunk/README.md
sed -i "s/^Commit:/Commit: $commit/" $ltrunk/README.md
sed -i "s/^Branch:/Branch: $branch/" $ltrunk/README.md
#git archive master config | tar -x -C $ltrunk
$here/fix-git-dates.py config $ltrunk $branch
$here/fix-git-dates.py setup_scripts $ltrunk $branch
$here/fix-git-dates.py docs $ltrunk $branch
$here/fix-git-dates.py tool-src $ltrunk $branch
$here/fix-git-dates.py distrib/skip-labs $ltrunk $branch
mkdir $scripts
$here/fix-git-dates.py scripts/labtainer-student $ltrunk $branch
$here/fix-git-dates.py scripts/labtainer-instructor $ltrunk $branch
mkdir $labs
llist=$(git ls-files labs | cut -d '/' -f 2 | uniq)
for lab in $llist; do
    if [ $(contains "${skiplist[@]}" $lab) != "y" ]; then
        $here/fix-git-dates.py labs/$lab/config $ltrunk $branch
        $here/fix-git-dates.py labs/$lab/instr_config $ltrunk $branch
        if [[ -d labs/$lab/docs ]]; then
            $here/fix-git-dates.py labs/$lab/docs $ltrunk $branch
        fi
        if [[ -d labs/$lab/bin ]]; then
            $here/fix-git-dates.py labs/$lab/bin $ltrunk $branch
        fi
    fi
done
distrib/mk-lab-pdf.sh $labs &> /tmp/mk-lab-pdf_$USER.log
result=$?
echo "result of mk-lab-pdf is $result"
if [ $result -ne 0 ]; then
    echo "Trouble making lab manuals"
    exit
fi
cd $ldir
if [[ -z $myshare ]]; then
    myshare=/media/sf_SEED/
fi

mv trunk/setup_scripts/install-labtainer.sh .
ln -s trunk/setup_scripts/update-labtainer.sh .
ln -s trunk/setup_scripts/update-designer.sh .

cd $ldir/trunk/tool-src/capinout
pwd
./mkit.sh &> /tmp/mkit_$USER.out
# put student and instructor guide at top of distribution.
cp $docs/student/labtainer-student.pdf $ldir/
cp $docs/instructor/labtainer-instructor.pdf $ldir/
cd $ddir
tar -cz -X $here/skip-labs -f $here/labtainer.tar labtainer
cd /tmp/
#tar -czf $here/labtainer_pdf.tar.gz labtainer_pdf
zip -qq -r $here/labtainer_pdf.zip labtainer_pdf
cd $here
cp labtainer.tar $myshare
cp labtainer_pdf.zip $myshare
if [[ "$1" == "-r" ]]; then
    mkdir -p artifacts
    cp labtainer.tar artifacts/
    cp labtainer_pdf.zip artifacts/
fi
echo "DONE"
