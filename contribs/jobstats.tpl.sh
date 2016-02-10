#!/bin/bash
#SBATCH --job-name=${name}
#SBATCH --ntasks=${ntasks}
#SBATCH --error=${error}
#SBATCH --output=${output}
#SBATCH --partition=${partition}
#SBATCH --time=${time}
#SBATCH --qos=${qos}
#SBATCH --wckey=${wckey}

# Slurm batch script to test batch scheduler availability and
# some FS access.

LOG_FILE=${log}
FSLIST="${fs}"

set -e

echo "`/bin/date` : start new job on `/bin/hostname`. "SLURM_JOB_ID = $SLURM_JOB_ID" "

for FS in ${FSLIST}
do
  cd $FS
  echo "`/bin/date` : test ${FS} - `/bin/pwd`"
done


if test -s ${error}
then
  echo "`/bin/date` : ERROR : "
  /bin/cat ${error} >> ${log}
else
  echo "`/bin/date` : No error messages";
fi

/bin/cat ${output} >> ${log}

/bin/rm ${output} ${error}

exit 0
