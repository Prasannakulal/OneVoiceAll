const mediasoup = require('mediasoup');
const WebSocket = require('ws');

// --- Configuration ---
const WS_CONTROL_PORT = 8082; // Port for the control plane

let worker;
const rooms = new Map(); // Stores { roomId: routerObject }

async function startMediasoup() {
    console.log('Starting Mediasoup worker...');
    worker = await mediasoup.createWorker({
        logLevel: 'warn',
    });

    worker.on('died', () => {
        console.error('Mediasoup worker has died!');
        process.exit(1);
    });

    // Create a default router for testing
    const router = await worker.createRouter({
        mediaCodecs: [
            { kind: 'audio', mimeType: 'audio/opus', clockRate: 48000, channels: 2 },
            { kind: 'video', mimeType: 'video/vp8', clockRate: 90000 },
        ]
    });
    rooms.set('default-room', router);

    console.log(`Mediasoup worker and default router are ready!`);
}

// --- Recording Infrastructure Logic ---
async function setupRecordingPipe(router, producerId) {
    // 1. Create a PipeTransport
    // This will tunnel the media stream out to an external process (like FFmpeg)
    const pipeTransport = await router.createPipeTransport({
        listenIp: '127.0.0.1' // Listen locally for the recording process
    });

    // For this setup, we are only creating the pipe. In a full implementation,
    // you would connect a specific user's media producer to this transport.

    const rtpPort = pipeTransport.tuple.localPort;
    console.log(`\n*** Recording pipe ready for producer ${producerId} ***`);
    console.log(`External recorder (e.g., FFmpeg) should listen on: 127.0.0.1:${rtpPort}`);
    console.log('----------------------------------------------------');

    return { pipeTransport, rtpPort };
}

// --- WebSocket Control Plane (for BE1 to send commands) ---
const wss = new WebSocket.Server({ port: WS_CONTROL_PORT });

wss.on('connection', ws => {
    console.log('Control plane client connected (e.g., from BE1).');

    ws.on('message', async message => {
        try {
            const data = JSON.parse(message);
            
            if (data.action === 'start-recording') {
                const router = rooms.get(data.roomId) || rooms.get('default-room');
                
                // For this test, we'll use a placeholder producerId
                const dummyProducerId = 'simulated-audio-stream';

                // Set up the recording pipe
                const { rtpPort } = await setupRecordingPipe(router, dummyProducerId);
                
                // Respond to the client (BE1) with the necessary port for FFmpeg
                ws.send(JSON.stringify({
                    status: 'recording-pipe-ready',
                    producerId: dummyProducerId,
                    rtpPort: rtpPort
                }));
            }
        } catch (error) {
            console.error('Error processing control command:', error.message);
            ws.send(JSON.stringify({ status: 'error', message: error.message }));
        }
    });
});

console.log(`Control plane listening for commands on ws://localhost:${WS_CONTROL_PORT}`);
startMediasoup();