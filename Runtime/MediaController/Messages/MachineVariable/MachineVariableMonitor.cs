// Visual Pinball Engine
// Copyright (C) 2025 freezy and VPE Team
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

using System;

namespace VisualPinball.Engine.Mpf.Unity.MediaController.Messages.MachineVariable
{
    public class MachineVariableMonitor<T> : MpfVariableMonitorBase<T, MachineVariableMessage>
        where T : IEquatable<T>
    {
        public MachineVariableMonitor(BcpInterface bcpInterface, string varName)
            : base(bcpInterface, varName) { }

        protected override string BcpCommand => MachineVariableMessage.Command;
    }
}
