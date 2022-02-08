const calculatorElement = document.getElementById('calculator');
const calculator = Desmos.GraphingCalculator(calculatorElement);

var defaultState;
var latex;
var height;
var width;
var download_images;
var total_frames;

xhr = new XMLHttpRequest();
const interval = setInterval(() => { // Attempt backend connection
    xhr.open('GET', `http://127.0.0.1:5000/init`);
    xhr.send();
}, 1000);

xhr.onload = () => { // Setup when backend connects successfully
    clearInterval(interval);
    latex = JSON.parse(xhr.response);
    height = latex.height;
    width = latex.width;
    total_frames = latex.total_frames;
    download_images = latex.download_images;

    var lastFrame = parseInt(sessionStorage.getItem('lastFrame')) || 0; // Get frame from page refresh
    sessionStorage.removeItem('lastFrame');

    calculator.setExpression({ id: 'frame', latex: `f=${lastFrame}`, color: '#2464b4', sliderBounds: { step: 1, max: total_frames, min: 0 } });
    calculator.setExpression({ id: 'lines', latex: 'l=0', color: '#2464b4' });
    if (lastFrame != 0) { // This is a refresh
        const viewport = JSON.parse(sessionStorage.getItem('viewport'));
        sessionStorage.removeItem('viewport');
        calculator.setViewport([viewport.xmin, viewport.xmax, viewport.ymin, viewport.ymax]);
        renderFrame(lastFrame);
    } else { // This is the first time loading the page
        var f = calculator.HelperExpression({ latex: 'f' });
        f.observe('numericValue', () => {
            if (Number.isNaN(f.numericValue) || f.numericValue <= 0) return;
            f.unobserve('numericValue');
            setTimeout(() => renderFrame(--f.numericValue), 3000); // Wait for additional keystrokes
        });
    }
    defaultState = calculator.getState(); // setBlank resets graph settings, this doesn't
    defaultState.graph.showGrid = defaultState.graph.showXAxis = defaultState.graph.showYAxis = latex.show_grid;
}

var loaded_frames = 0; // All frames loaded from backend so far
var old_frames = 0; // Frames rendered prior to last backend request
function renderFrame(frame) {
    if (frame >= total_frames) return; // Animation finished
    if (loaded_frames == 0) { // Load a batch of frames
        xhr = new XMLHttpRequest();
        xhr.open('GET', `http://127.0.0.1:5000/?frame=${frame}`);
        xhr.send();
        xhr.onload = () => {
            latex = JSON.parse(xhr.response);
            if (latex.result === null) return;
            loaded_frames = frame + latex.number_of_frames;
            old_frames = frame;
            renderFrame(frame);
        }
    } else { // Render the next frame
        const viewport = calculator.getState().graph.viewport;
        var start = Date.now();
        calculator.setState(defaultState);
        calculator.setExpression( { id: 'frame', latex: 'f=' + (frame + 1) } );
        calculator.setExpression( { id: 'lines', latex: 'l=' + latex.result[frame - old_frames].length});
        console.log('Lines for frame ' + (frame + 1) + ': ' + latex.result[frame - old_frames].length);
        calculator.setViewport([viewport.xmin, viewport.xmax, viewport.ymin, viewport.ymax]); // setState resets the viewport, set it back to what it was
        console.log('adding ' + (Date.now() - start) / 1000);
        setTimeout(() => {
            calculator.setExpressions(latex.result[frame - old_frames]);
            console.log('drawing ' + (Date.now() - start) / 1000);

            const params = {
                mode: 'stretch',
                mathBounds: { left: 0, bottom: 0, right: width, top: height },
                width: width,
                height: height,
                targetPixelRatio: 1
            }
            calculator.asyncScreenshot(params, screenshot => handleScreenshot(screenshot, start, ++frame)); // Waits for frame to render, takes a screenshot and runs handleScreenshot
        }, 100); // Slight delay to allow the list to update
    }
}

const imgcont = document.createElement('a');
document.body.appendChild(imgcont);
async function handleScreenshot(screenshot, start, frame) {
    console.log('done ' + (Date.now() - start) / 1000);
    imgcont.href = screenshot;
    imgcont.download = 'frame-' + String(frame).padStart(5, '0');
    imgcont.innerHTML = `<img src= ${screenshot}>`;
    if (download_images) imgcont.click();

    // Reloading the page every so often seems to reduce random slowdowns
    if (frame >= loaded_frames) {
        sessionStorage.setItem('lastFrame', frame);
        sessionStorage.setItem('viewport', JSON.stringify(calculator.getState().graph.viewport));
        location.reload();
    } else renderFrame(frame);
}

