import redux.pipeline

from redux.pipes import Read, Power, Mask, Shape, Scale, Format, LPF, Sqrt, Pad

class StandardPipeline(redux.pipeline.Pipeline):
	pipeorder = [
		Read,
		Pad,
		Power,
		Shape,
		Mask,
		Sqrt,
		LPF,
		Scale,
		Format,
	]
