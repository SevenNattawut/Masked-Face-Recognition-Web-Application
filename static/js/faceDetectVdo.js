// // create and initialize video element
// const video = document.createElement('video')

// video.muted = true
// video.autoplay = true

// // start video
// function startVideo() {
//     navigator.getUserMedia(
//         { video: {} },
//         stream => video.srcObject = stream,
//         err => console.log(err)
//     )
// }

// startVideo()

// video.addEventListener('play', () => {
//     let canvas = document.getElementById('#vdoCanvas')
//     let ctx = canvas.getContext('2d')

//     setInterval(async () => {
//         ctx.drawImage(video, 0, 0);
//     }, 100)
// })

function openCvReady() {
    cv['onRuntimeInitialized'] = () => {
        let video = document.getElementById("videoInput")
            navigator.mediaDevices.getUserMedia({ video: true, audio: false })
            .then(function (stream) {                    
                video.srcObject = stream;
                video.play();
            })
            .catch(function (err) {
                console.log("An error occurred! " + err);
            });
        video.addEventListener('loadedmetadata', function () {
            if (video.width * video.height > 0) {
                let src = new cv.Mat(video.height, video.width, cv.CV_8UC4);
                let dst = new cv.Mat(video.height, video.width, cv.CV_8UC1);
                let gray = new cv.Mat();
                let cap = new cv.VideoCapture("videoInput");
                let faces = new cv.RectVector();
                let classifier = new cv.CascadeClassifier();
                let utils = new Utils('errorMessage');
                let faceCascadeFile = 'static/models/haar_cascade/haarcascade_frontalface_default.xml';
                utils.createFileFromUrl(faceCascadeFile, faceCascadeFile, () => {
                    classifier.load(faceCascadeFile); // in the callback, load the cascade from file 
                });
                const FPS = 60;
                function processVideo() {
                    let begin = Date.now();
                    cap.read(src);
                    src.copyTo(dst);
                    cv.cvtColor(dst, gray, cv.COLOR_RGBA2GRAY, 0);
                    if (capture){
                        // find face, if found, crop face image, save to json, then draw rectangle to the uncropped frame and write "CAPTURE" to the top-left of the frame
                        try {
                            classifier.detectMultiScale(gray, faces, 1.1, 3, 0);
                            //console.log(faces.size());
                        } catch (err) {
                            console.log(err);
                        }
                        
                        for (let i = 0; i < faces.size(); ++i) {
                            let face = faces.get(i);
                            let point1 = new cv.Point(face.x, face.y);
                            let point2 = new cv.Point(face.x + face.width, face.y + face.height);
                            cv.rectangle(dst, point1, point2, [255, 0, 0, 255]);
                        }

                        // Add "CAPTURE" text to top-left of the frame
                            cv.putText(dst, "CAPTURE", new cv.Point(10, 50), cv.FONT_HERSHEY_SIMPLEX, 1.5, [255, 0, 0, 255], 2);
                        }
                        else{
                            // Add "LIVE" text to top-left of the frame
                            cv.putText(dst, "LIVE", new cv.Point(10, 50), cv.FONT_HERSHEY_SIMPLEX, 1.5, [255, 0, 0, 255], 2);
                        }
                        
                    
                    cv.imshow("vdoCanvas", dst);
                    // schedule next one.
                    let delay = 1000 / FPS - (Date.now() - begin);
                    setTimeout(processVideo, delay);
                }
                // schedule first one.
                setTimeout(processVideo, 0);
            }
        });
    };
}