#!/usr/bin/python


import os
import cv2
import numpy as np
import math
import sys
import fnmatch
from skimage import io,draw,data
# Read points from text files in directory
def readPoints(path) :
    # Create an array of array of points.
    pointsArray = [];

    #List all files in the directory and read points from text files one by one
    for filePath in os.listdir(path):
        
        if filePath.endswith(".txt"):
            
            #Create an array of points.
            points = [];            
            
            # Read points from filePath
            with open(os.path.join(path, filePath)) as file :
                for line in file :
                    x, y = line.split()
                    points.append((int(x), int(y)))
            
            # Store array of points
            pointsArray.append(points)
            
    return pointsArray;

def readAImagePoints(filePath):
    if filePath.endswith(".txt"):

        # Create an array of points.
        points = [];

        # Read points from filePath
        with open(os.path.join(path, filePath)) as file:
            for line in file:
                x, y = line.split()
                points.append((int(x), int(y)))

        return points;
    else:
        return None;

def readAImage(filePath):
    if filePath.endswith(".jpg"):
        # Read image found.
        img = cv2.imread(os.path.join(path, filePath));

        # Convert to floating point
        img = np.float32(img) / 255.0;
        return img;
    else:
        print("failed to read image.")
        return None;

# Read all jpg images in folder.
def readImages(path) :
    
    #Create array of array of images.
    imagesArray = [];
    
    #List all files in the directory and read points from text files one by one
    for filePath in os.listdir(path):
        #if filePath.endswith(".jpg"):
            # Read image found.
        #    img = cv2.imread(os.path.join(path,filePath));

            # Convert to floating point
        #    img = np.float32(img)/255.0;
        img = readAImage((filePath))

        # Add to array of images
        if img != None:
            imagesArray.append(img);
            
    return imagesArray;
                
# Compute similarity transform given two sets of two points.
# OpenCV requires 3 pairs of corresponding points.
# We are faking the third one.

def similarityTransform(inPoints, outPoints) :
    s60 = math.sin(60*math.pi/180);
    c60 = math.cos(60*math.pi/180);  
  
    inPts = np.copy(inPoints).tolist();
    outPts = np.copy(outPoints).tolist();
    
    xin = c60*(inPts[0][0] - inPts[1][0]) - s60*(inPts[0][1] - inPts[1][1]) + inPts[1][0];
    yin = s60*(inPts[0][0] - inPts[1][0]) + c60*(inPts[0][1] - inPts[1][1]) + inPts[1][1];
    
    inPts.append([np.int(xin), np.int(yin)]);
    
    xout = c60*(outPts[0][0] - outPts[1][0]) - s60*(outPts[0][1] - outPts[1][1]) + outPts[1][0];
    yout = s60*(outPts[0][0] - outPts[1][0]) + c60*(outPts[0][1] - outPts[1][1]) + outPts[1][1];
    
    outPts.append([np.int(xout), np.int(yout)]);
    
    tform ,_= cv2.estimateAffinePartial2D(np.array([inPts]), np.array([outPts]), False);
    
    return tform;


# Check if a point is inside a rectangle
def rectContains(rect, point) :
    if point[0] < rect[0] :
        return False
    elif point[1] < rect[1] :
        return False
    elif point[0] > rect[2] :
        return False
    elif point[1] > rect[3] :
        return False
    return True

# Calculate delanauy triangle
def calculateDelaunayTriangles(rect, points):
    # Create subdiv
    subdiv = cv2.Subdiv2D(rect);
   
    # Insert points into subdiv
    for p in points:
        subdiv.insert((p[0], p[1]));

   
    # List of triangles. Each triangle is a list of 3 points ( 6 numbers )
    triangleList = subdiv.getTriangleList();

    # Find the indices of triangles in the points array

    delaunayTri = []
    
    for t in triangleList:
        pt = []
        pt.append((t[0], t[1]))
        pt.append((t[2], t[3]))
        pt.append((t[4], t[5]))
        
        pt1 = (t[0], t[1])
        pt2 = (t[2], t[3])
        pt3 = (t[4], t[5])        
        
        if rectContains(rect, pt1) and rectContains(rect, pt2) and rectContains(rect, pt3):
            ind = []
            for j in range(0, 3):
                for k in range(0, len(points)):                    
                    if(abs(pt[j][0] - points[k][0]) < 1.0 and abs(pt[j][1] - points[k][1]) < 1.0):
                        ind.append(k)                            
            if len(ind) == 3:                                                
                delaunayTri.append((ind[0], ind[1], ind[2]))
        

    
    return delaunayTri


def constrainPoint(p, w, h) :
    p =  ( min( max( p[0], 0 ) , w - 1 ) , min( max( p[1], 0 ) , h - 1 ) )
    return p;

# Apply affine transform calculated using srcTri and dstTri to src and
# output an image of size.
def applyAffineTransform(src, srcTri, dstTri, size) :
    
    # Given a pair of triangles, find the affine transform.
    warpMat = cv2.getAffineTransform( np.float32(srcTri), np.float32(dstTri) )
    
    # Apply the Affine Transform just found to the src image
    dst = cv2.warpAffine( src, warpMat, (size[0], size[1]), None, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101 )

    return dst


# Warps and alpha blends triangular regions from img1 and img2 to img
def warpTriangle(img1, img2, t1, t2) :

    # Find bounding rectangle for each triangle
    r1 = cv2.boundingRect(np.float32([t1]))
    r2 = cv2.boundingRect(np.float32([t2]))

    # Offset points by left top corner of the respective rectangles
    t1Rect = [] 
    t2Rect = []
    t2RectInt = []

    for i in range(0, 3):
        t1Rect.append(((t1[i][0] - r1[0]),(t1[i][1] - r1[1])))
        t2Rect.append(((t2[i][0] - r2[0]),(t2[i][1] - r2[1])))
        t2RectInt.append(((t2[i][0] - r2[0]),(t2[i][1] - r2[1])))


    # Get mask by filling triangle
    mask = np.zeros((r2[3], r2[2], 3), dtype = np.float32)
    cv2.fillConvexPoly(mask, np.int32(t2RectInt), (1.0, 1.0, 1.0), 16, 0);

    # Apply warpImage to small rectangular patches
    img1Rect = img1[r1[1]:r1[1] + r1[3], r1[0]:r1[0] + r1[2]]
    
    size = (r2[2], r2[3])

    img2Rect = applyAffineTransform(img1Rect, t1Rect, t2Rect, size)
    
    img2Rect = img2Rect * mask

    # Copy triangular region of the rectangular patch to the output image
    img2[r2[1]:r2[1]+r2[3], r2[0]:r2[0]+r2[2]] = img2[r2[1]:r2[1]+r2[3], r2[0]:r2[0]+r2[2]] * ( (1.0, 1.0, 1.0) - mask )
     
    img2[r2[1]:r2[1]+r2[3], r2[0]:r2[0]+r2[2]] = img2[r2[1]:r2[1]+r2[3], r2[0]:r2[0]+r2[2]] + img2Rect





if __name__ == '__main__' :

    if len(sys.argv) < 2:
        print(
            "For example, if you are in the python_examples folder then "
            "execute this program by running:\n"
            "python scripts\average_face_generation.py input_data\president [output_data\president.jpg]\n")
        exit()

    path = sys.argv[1]

    average_pic_name = 'output_data\myaverageface.jpg'

    if len(sys.argv) == 3:
        average_pic_name = sys.argv[2]

    # Dimensions of output image
    w = 600;
    h = 600;

    # Read points for all images
    #allPoints = readPoints(path);
    
    # Read all images
    #images = readImages(path);
    
    # Eye corners
    eyecornerDst = [ (np.int(0.3 * w ), np.int(h / 3)), (np.int(0.7 * w ), np.int(h / 3)) ];
    
    imagesNorm = [];
    pointsNorm = [];
    
    # Add boundary points for delaunay triangulation
    boundaryPts = np.array([(0,0), (w/2,0), (w-1,0), (w-1,h/2), ( w-1, h-1 ), ( w/2, h-1 ), (0, h-1), (0,h/2) ]);
    
    # Initialize location of average points to 0s
    pointsAvg = [];
    
    #n = len(allPoints[0]);

    numPoints =  len(fnmatch.filter(os.listdir(path), '*.txt'))

    #numImages = len(images)
    #numPoints = len(allPoints)
    # Warp images and trasnform landmarks to output coordinate system,
    # and find average of transformed landmarks.
    #print "image number is {}".format(numPoints)

    #for i in xrange(0, numPoints):
    imgl=[]
    index = 0;
    for filePath in os.listdir(path):
        if filePath.endswith(".txt"):
            points1 = readAImagePoints(filePath);

            if index == 0:
                pointsAvg = np.array([(0, 0)] * (len(points1) + len(boundaryPts)), np.float32());

            imageFilePath = filePath.replace(".txt", "").lower();
            #print "read {}".format(imageFilePath)
            image = readAImage(imageFilePath);
            
            # Corners of the eye in input image
            eyecornerSrc  = [ points1[36], points1[45] ] ;
        
            # Compute similarity transform
            tform = similarityTransform(eyecornerSrc, eyecornerDst);
        
            # Apply similarity transformation
            img = cv2.warpAffine(image, tform, (w,h));
            imgl.append(img)
            # Apply similarity transform on points
            points2 = np.reshape(np.array(points1), (68,1,2));
        
            points = cv2.transform(points2, tform);
        
            points = np.float32(np.reshape(points, (68, 2)));
        
            # Append boundary points. Will be used in Delaunay Triangulation
            points = np.append(points, boundaryPts, axis=0)
        
            # Calculate location of average landmark points.
            pointsAvg = pointsAvg + points / numPoints;
        
            pointsNorm.append(points);
            imagesNorm.append(img);

            index = index + 1;

    
    # Delaunay triangulation
    rect = (0, 0, w, h);
    dt = calculateDelaunayTriangles(rect, np.array(pointsAvg));
    # Output image
    output = np.zeros((h,w,3), np.float32());

    # Warp input images to average image landmarks
    for i in range(0, len(imagesNorm)) :
        img = np.zeros((h,w,3), np.float32());
        # Transform triangles one by one
        tinl=[];
        toutl=[]
        for j in range(0, len(dt)) :
            tin = []; 
            tout = [];
            # print(dt[j])
            for k in range(0, 3) :                
                pIn = pointsNorm[i][dt[j][k]];
                pIn = constrainPoint(pIn, w, h);
                # print(pIn)
                pOut = pointsAvg[dt[j][k]];
                pOut = constrainPoint(pOut, w, h);
                # print(pOut)
                tin.append(pIn);
                tout.append(pOut);
            tinl.append(tin)
            toutl.append(tout)
            warpTriangle(imagesNorm[i], img, tin, tout);
        newf="F:\\postgraduate\\practice\\rerun\\dataset\\data\\AverageFace-master\\input_data\\{}.jpg".format(i)
        newf1="F:\\postgraduate\\practice\\rerun\\dataset\\data\\AverageFace-master\\input_data\\{}.jpg".format(i+20)
        newf2="F:\\postgraduate\\practice\\rerun\\dataset\\data\\AverageFace-master\\input_data\\ave.jpg"
        img1 = np.zeros((h,w,3), np.float32());
        img1.fill(255)
        for k in range(0, len(dt)):
        #     cv2.line(img, (int(toutl[k][0][0]), int(toutl[k][0][1])), (int(toutl[k][1][0]), int(toutl[k][1][1])), (255,0,0),thickness=2)
        #     cv2.line(img, (int(toutl[k][1][0]), int(toutl[k][1][1])), (int(toutl[k][2][0]), int(toutl[k][2][1])), (255,0,0),thickness=2)
        #     cv2.line(img, (int(toutl[k][2][0]), int(toutl[k][2][1])), (int(toutl[k][0][0]), int(toutl[k][0][1])), (255,0,0),thickness=2)
        #     cv2.line(imgl[i], (int(tinl[k][0][0]), int(tinl[k][0][1])), (int(tinl[k][1][0]), int(tinl[k][1][1])), (255,0,0),thickness=2)
        #     cv2.line(imgl[i], (int(tinl[k][1][0]), int(tinl[k][1][1])), (int(tinl[k][2][0]), int(tinl[k][2][1])), (255,0,0),thickness=2)
        #     cv2.line(imgl[i], (int(tinl[k][2][0]), int(tinl[k][2][1])), (int(tinl[k][0][0]), int(tinl[k][0][1])), (255,0,0),thickness=2)
            # break
            # cv2.circle(imgl[i], (int(tinl[k][0][0]), int(tinl[k][0][1])), 3, (255, 0, 0), 3)
            # cv2.circle(imgl[i], (int(tinl[k][1][0]), int(tinl[k][1][1])), 3, (255, 0, 0), 3)
            # cv2.circle(imgl[i], (int(tinl[k][2][0]), int(tinl[k][2][1])), 3, (255, 0, 0), 3)
            # cv2.circle(img1, (int(toutl[k][0][0]), int(toutl[k][0][1])), 3, (255, 0, 0), 10)
            # cv2.circle(img1, (int(toutl[k][1][0]), int(toutl[k][1][1])), 3, (255, 0, 0), 10)
            # cv2.circle(img1, (int(toutl[k][2][0]), int(toutl[k][2][1])), 3, (255, 0, 0), 10)
            cv2.line(img1, (int(toutl[k][0][0]), int(toutl[k][0][1])), (int(toutl[k][1][0]), int(toutl[k][1][1])), (255,0,0),thickness=2)
            cv2.line(img1, (int(toutl[k][1][0]), int(toutl[k][1][1])), (int(toutl[k][2][0]), int(toutl[k][2][1])), (255,0,0),thickness=2)
            cv2.line(img1, (int(toutl[k][2][0]), int(toutl[k][2][1])), (int(toutl[k][0][0]), int(toutl[k][0][1])), (255,0,0),thickness=2)
        # cv2.imshow('image',img)
        # cv2.waitKey(0)
        # cv2.imshow('image',imgl[i])
        # cv2.waitKey(0)
        # cv2.imwrite(newf, (img * 255))
        cv2.imwrite(newf2, (img1 * 255))
        # io.imsave(newf, imgl[i])

        # Add image intensities for averaging
        output = output + img;
        # cv2.imwrite(newf, (img * 255).astype('uint8'))

    # Divide by numImages to get average
    output = output / numPoints;

    # Save result
    cv2.imwrite(average_pic_name, (output * 255).astype('uint8'))
