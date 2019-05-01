fes <- function(step) {
  ifilename<-paste("fes",toString(step), sep="")
  ifilename<-paste(ifilename, ".txt", sep="")
  ifile <- read.table(ifilename)
  mat<-t(matrix(ifile[,3], nrow=48))
  mat<-cbind(mat, mat[,1])
  mat<-rbind(mat, mat[1,])
  image(-24:24*7.5, -24:24*7.5, mat,
        xlab="phi", ylab="psi", zlim=c(0,25), main="",
        col=rainbow(70)[50:1], axes=F, lwd=2)
  contour(-24:24*7.5, -24:24*7.5, mat, xlab="phi", ylab="psi", zlim=c(0,25), nlevels=5, add=T, main="", lwd=2)
  axis(1, at=60*(-3:3), lwd=2)
  axis(2, at=60*(-3:3), lwd=2)
  box(lwd=2)
}

png("fes%03d.png", width=960, height=960, pointsize=24)
for(i in 0:500) {
  fes(i)
}
dev.off()
