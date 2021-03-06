plot.single.file <- function(
	dir=".",
	#dir="/home/dlevin/Documents/sdnctrlsim/logs/", 
	#dir = "//mnt/raid5_data/stanford-ofnet/virtpyenv/logs/",
	#file="anja_rmse_sync_improves_metric_lbc_wave_32_0.txt",
	file,
	filesuffix="",
	slice.start = 112,
	slice.length = 35,
	do.ps=0, psdir="/tmp/", psbase="", m.max=1000, n=4, do.boxplot=0, do.ts=1)
{

  filename = paste(dir, "/", file, filesuffix, sep = "")
  cat("reading", filename, "\n")
  data <- read.file(filename, n)

  if(do.ts) {
    if(do.ps) {
      psname <- paste(psdir, psbase, file, "_ts.pdf", sep = "")
      ps.init(psname)
    }
#    xrange <- c(1,length(data[,1]))
#    yrange <- range(data)
# TODO: Make the start:end values parameters
    #xrange <- c(1,length(data[,1][slice.start:(slice.start+slice.length)]))
    xrange <- c(slice.start, slice.start+slice.length)
    yrange <- range(data)
    plot(xrange, yrange, xlab = "Simulation Time", 
      	ylab = "% Link Utilization", type = "n",
      	cex = 2, cex.axis = 2, cex.lab = 2)
	leg = paste("Link ", c("sw1 - sw2", "srv1 - sw1", "srv2 - sw2", "sw2 - sw1"))
    do.col <- c(1:n, 1:n)
    legend(x=slice.start+2, y=0.3, col=do.col[1:n], pch=c(1:n), legend=leg, bty="n", lty=rep(1, n), cex=1.5)
    for(i in 1:n) {
	  xvals = c(slice.start:(slice.start+slice.length))
      points(xvals, data[, i][slice.start:(slice.start+slice.length)], col = do.col[i], pch = i, cex = 2)
      lines(xvals, data[, i][slice.start:(slice.start+slice.length)], col = do.col[i], pch = i, cex = 2)
    }
    abline(v=c(0:16)*16+1)
    if(do.ps) {
      dev.off()
    }
  }
  else {
    mywait(-1)
  }

  if (do.boxplot) {
	  if(do.ps) {
		psname <- paste(psdir, psbase, file, "_boxplot.pdf", sep = "")
		ps.init(psname)
	  }

    box.cutoff <- length(data[,1])
    #box.yrange <- range(data[16:box.cutoff,])
    box.yrange <- c(0,8)
	box.names <- c(0, 2**c(0:4))
    boxplot(data[16:box.cutoff,], names=box.names, ylim = box.yrange, xlab="NOS Sync Period (Simulation Timesteps)", ylab="Server Link RMSE", cex=2, cex.axis=2, cex.lab=2)
	abline(h=0.707, lty=2)
    #title(file)

    if(do.ps) {
      dev.off()
    }
  }
}

mywait <- function(how.long = options()$wait)
{
        if(is.null(how.long))
                how.long <- 10
        if(how.long < 0) {
                cat("Press <return> to continue: ")
                h <- readline()
                cat("readline result: ", h, "\n")
                if(h == "a") {
                        exit()
                }
        }
        else unix(paste("sleep", how.long))
        if(0 && exists(".Device")) {
                par(mfrow = c(1, 1), col = 1)
        }
        # If there is a device, reset the graphics parameters
        invisible(how.long)
}


ps.init <-
function(filename, w = 10, h = 5.625, margins = c(4, 5, 0, 5))
{
        if(h > 0 && w > 0) {
                pdf(filename, height=h, width=w)
        }
        else {
                pdf(filename)
        }
        par(lwd = 2.)
        if(length(margins) > 0) {
                par(mar = margins)
        }
#        else {
#			if(do.mar[1] > 0)
#				par(mar = do.mar)
#        }
}


read.file <-
function(name, n, skip = 1)
{
        matrix(scan(name, skip = skip), ncol = n, byrow = T)
}
